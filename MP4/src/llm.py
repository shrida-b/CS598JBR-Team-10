"""OpenAI-compatible chat client with a quota-aware model cascade.

Models are tried in config order (active provider first, then
`provider_fallbacks` whose API key is set). Per model we enforce RPM / input-TPM,
keep a per-day request ledger (RPD), skip models whose daily quota is used up,
retry transient 5xx and cool down overloaded models.
"""
from __future__ import annotations

import collections
import copy
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from common import MP4, estimate_tokens, pacific_date

DUMMY_SIGNATURE = "skip_thought_signature_validator"   # documented Gemini escape hatch
COOLDOWN_SECONDS = 300


class QuotaExhausted(Exception):
    """No configured model has quota/budget left (the run can resume later)."""


class LLMError(Exception):
    pass


class ModelPool:
    def __init__(self, cfg: dict, trajectory, provider: str | None = None):
        self.cfg = cfg
        self.inf = cfg["inference"]
        self.traj = trajectory
        active = provider or cfg["model"]["provider"]
        order = [active] + [p for p in cfg["model"]["provider_fallbacks"] if p != active]
        self.candidates = []           # (provider, model_cfg)
        for p in order:
            pc = cfg["providers"][p]
            if pc["api_key_env"] and not os.environ.get(pc["api_key_env"]):
                continue
            for m in pc["models"]:
                self.candidates.append((p, m))
        if not self.candidates:
            raise LLMError(f"no provider usable: set the API key for {order}")
        self.ledger_path = MP4 / cfg["model"]["quota_ledger"]
        self.ledger = self._load_ledger()
        self.recent = collections.defaultdict(collections.deque)   # key -> deque[(t, tokens)]
        self.cooldown: dict[str, float] = {}
        self.run_requests = collections.Counter()                   # provider -> requests this run

    # ------------------------------------------------------------- ledger
    def _load_ledger(self) -> dict:
        try:
            led = json.loads(self.ledger_path.read_text())
        except (OSError, ValueError):
            led = {}
        if led.get("date") != pacific_date():
            led = {"date": pacific_date(), "counts": {}, "exhausted": []}
        return led

    def _save_ledger(self) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(json.dumps(self.ledger, indent=1))

    def _count(self, key: str) -> int:
        if self.ledger.get("date") != pacific_date():      # day rolled over mid-run
            self.ledger = {"date": pacific_date(), "counts": {}, "exhausted": []}
        return self.ledger["counts"].get(key, 0)

    def _available(self, provider: str, model: dict) -> bool:
        pc = self.cfg["providers"][provider]
        key = f"{provider}/{model['id']}"
        if self.run_requests[provider] >= pc["max_requests_per_run"]:
            return False
        if key in self.ledger["exhausted"]:
            return False
        if model.get("rpd") and self._count(key) >= model["rpd"]:
            return False
        if pc.get("rpd"):
            shared = sum(v for k, v in self.ledger["counts"].items() if k.startswith(provider + "/"))
            if shared >= pc["rpd"]:
                return False
        return self.cooldown.get(key, 0) <= time.time()

    def budget_left(self) -> bool:
        return any(self._available(p, m) or self.cooldown.get(f"{p}/{m['id']}", 0) > time.time()
                   for p, m in self.candidates)

    # ------------------------------------------------------------- throttle
    def _throttle(self, provider: str, model: dict, est_tokens: int) -> None:
        pc = self.cfg["providers"][provider]
        rpm = model.get("rpm") or pc.get("rpm") or 0
        tpm = model.get("tpm") or 0
        key = f"{provider}/{model['id']}" if model.get("rpm") else provider
        dq = self.recent[key]
        while True:
            now = time.time()
            while dq and now - dq[0][0] > 60:
                dq.popleft()
            over_rpm = rpm and len(dq) >= rpm
            over_tpm = tpm and dq and sum(t for _, t in dq) + est_tokens > tpm * 0.9
            if not (over_rpm or over_tpm):
                break
            time.sleep(max(1.0, 60 - (now - dq[0][0]) + 1))
        dq.append((time.time(), est_tokens))

    # ------------------------------------------------------------- request
    @staticmethod
    def _prepare_messages(messages: list, provider: str) -> list:
        msgs = copy.deepcopy(messages)
        for m in msgs:
            for tc in m.get("tool_calls") or []:
                if provider == "gemini":
                    # Gemini requires a thought signature on every replayed tool call;
                    # calls produced by another provider get the documented placeholder.
                    tc.setdefault("extra_content", {"google": {"thought_signature": DUMMY_SIGNATURE}})
                else:
                    tc.pop("extra_content", None)
            if provider != "gemini":
                m.pop("extra_content", None)
        return msgs

    def _post(self, provider: str, body: dict) -> dict:
        pc = self.cfg["providers"][provider]
        headers = {"Content-Type": "application/json"}
        if pc["api_key_env"]:
            headers["Authorization"] = "Bearer " + os.environ[pc["api_key_env"]]
        req = urllib.request.Request(pc["base_url"].rstrip("/") + "/chat/completions",
                                     data=json.dumps(body).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.inf["request_timeout_seconds"]) as resp:
            return json.loads(resp.read().decode())

    def chat(self, messages: list, tools: list) -> tuple[dict, dict]:
        """Return (assistant_message, meta). Raises QuotaExhausted when nothing is left."""
        waited = 0.0
        while True:
            for provider, model in self.candidates:
                if not self._available(provider, model):
                    continue
                result = self._try_model(provider, model, messages, tools)
                if result is not None:
                    return result
            # Nothing succeeded: wait for a cooldown if one will expire soon.
            pending = [t for t in self.cooldown.values() if t > time.time()]
            if pending and waited < 1800:
                pause = min(pending) - time.time() + 1
                self.traj.event("llm_wait", seconds=round(pause), reason="all models cooling down")
                time.sleep(pause)
                waited += pause
                continue
            raise QuotaExhausted("all configured models are out of daily quota or run budget")

    def _try_model(self, provider, model, messages, tools):
        pc = self.cfg["providers"][provider]
        key = f"{provider}/{model['id']}"
        body = {
            "model": model["id"],
            "messages": self._prepare_messages(messages, provider),
            "tools": tools,
            "tool_choice": self.inf["tool_choice"],
            "temperature": self.inf["temperature"],
            "top_p": self.inf["top_p"],
            "max_tokens": self.inf["max_tokens"],
            "seed": self.inf["seed"],
            "parallel_tool_calls": self.inf["parallel_tool_calls"],
        }
        for p in pc.get("unsupported_params", []):
            body.pop(p, None)
        est = estimate_tokens(body["messages"]) + estimate_tokens(tools)
        waits = list(self.cfg["model"]["retry_on_5xx_seconds"])
        rate_retry_done = False
        while True:
            self._throttle(provider, model, est)
            start = time.time()
            try:
                resp = self._post(provider, body)
            except urllib.error.HTTPError as e:
                text = e.read().decode(errors="replace")
                self.traj.event("llm_error", provider=provider, model=model["id"], http=e.code, body=text[:600])
                self._record(key, provider)          # failed calls still count against quota
                if e.code == 429:
                    if "day" in text.lower() or "PerDay" in text:
                        self.ledger["exhausted"].append(key)
                        self._save_ledger()
                        return None
                    if not rate_retry_done:
                        rate_retry_done = True
                        time.sleep(pc.get("retry_on_429_seconds", 60))
                        continue
                    self.cooldown[key] = time.time() + COOLDOWN_SECONDS
                    return None
                if e.code >= 500:
                    if waits:
                        time.sleep(waits.pop(0))
                        continue
                    self.cooldown[key] = time.time() + COOLDOWN_SECONDS
                    return None
                # 4xx other than 429: request problem for this model -> try the next one
                self.cooldown[key] = time.time() + COOLDOWN_SECONDS
                return None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                self.traj.event("llm_error", provider=provider, model=model["id"], error=str(e))
                if waits:
                    time.sleep(waits.pop(0))
                    continue
                self.cooldown[key] = time.time() + COOLDOWN_SECONDS
                return None
            self._record(key, provider)
            try:
                msg = resp["choices"][0]["message"]
                finish = resp["choices"][0].get("finish_reason")
            except (KeyError, IndexError, TypeError):
                self.traj.event("llm_error", provider=provider, model=model["id"], error="malformed response",
                                body=json.dumps(resp)[:600])
                self.cooldown[key] = time.time() + 60
                return None
            usage = resp.get("usage") or {}
            if usage.get("prompt_tokens"):
                dq = self.recent[key if model.get("rpm") else provider]
                if dq:
                    dq[-1] = (dq[-1][0], usage["prompt_tokens"])
            msg = {k: v for k, v in msg.items() if v is not None}
            msg["role"] = "assistant"
            meta = {"provider": provider, "model": resp.get("model") or model["id"], "requested_model": model["id"],
                    "usage": usage, "finish_reason": finish, "seconds": round(time.time() - start, 1),
                    "requests_today": self._count(key)}
            return msg, meta

    def _record(self, key: str, provider: str) -> None:
        self._count(key)
        self.ledger["counts"][key] = self.ledger["counts"].get(key, 0) + 1
        self.run_requests[provider] += 1
        self._save_ledger()
