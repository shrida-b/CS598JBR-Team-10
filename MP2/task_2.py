import ast
import copy
import importlib.util
import json
import os
import re
import subprocess
import sys

import jsonlines
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

#####################################################
# MP2 - Task 2: Test generation
#####################################################

BASE_SYSTEM_PROMPT = (
    "You are an AI programming assistant. You are an AI programming assistant, "
    "utilizing the DeepSeek Coder model, developed by DeepSeek Company, and you "
    "only answer questions related to computer science. For politically sensitive "
    "questions, security and privacy issues, and other non-computer science "
    "questions, you will refuse to answer."
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COVERAGE_DIR = os.path.join(SCRIPT_DIR, "Coverage")      # -> MP2/Coverage
WORK_DIR = os.path.join(SCRIPT_DIR, "generated_tests")   # scratch: {ID}.py / {ID}_test.py


def save_file(content, file_path):
    with open(file_path, "w") as file:
        file.write(content)


# ----------------------------------------------------------------------------
# Prompts
# ----------------------------------------------------------------------------
def _safe_id(task_id):
    """'HumanEval/139' -> 'HumanEval_139' (valid file / module name)."""
    return task_id.replace("/", "_")


def _program_source(entry):
    return entry["prompt"].rstrip() + "\n" + entry["canonical_solution"].rstrip() + "\n"


def build_prompt(entry, vanilla=True):
    program = _program_source(entry)
    fn = entry["entry_point"]
    module = _safe_id(entry["task_id"])

    if vanilla:
        instruction = (
            "Generate a pytest test suite for the following code.\n"
            "Only write unit tests in the output and nothing else.\n\n"
            f"{program}"
        )
    else:
        instruction = (
            "Generate a pytest test suite for the following Python code. "
            "The goal is to reach 100% line and branch coverage.\n\n"
            "Requirements:\n"
            f"1. Start with `import pytest` and `from {module} import {fn}`.\n"
            "2. Write about 8 to 12 test functions named test_<something>. Every test must use "
            "different inputs and contain only a few closely related asserts.\n"
            "3. Make sure every branch, loop path and return statement of the code is executed "
            "by at least one test: empty or minimal inputs, boundary values, and an input for "
            "each if/else/early return.\n"
            "4. The docstring examples are guaranteed correct, so reuse them as tests.\n"
            "5. Only test inputs that the docstring says are valid. Do not test for exceptions, "
            "and do not use huge numbers or very long strings.\n"
            "6. Before writing each expected value, mentally trace the code step by step on that "
            "exact input and write the value the CODE returns. Prefer small inputs that are easy "
            "to trace.\n"
            "7. Only write the Python test code in one ```python block and nothing else.\n\n"
            "Example of the expected style (for a different function):\n"
            "```python\n"
            "import pytest\n"
            "from example import add_pos\n\n"
            "def test_add_pos_basic():\n    assert add_pos(2, 3) == 5\n\n"
            "def test_add_pos_zero():\n    assert add_pos(0, 0) == 0\n\n"
            "def test_add_pos_negative_branch():\n    assert add_pos(-1, 3) == 3\n"
            "```\n\n"
            f"Now write the test suite for this code:\n\n{program}"
        )

    return f"{BASE_SYSTEM_PROMPT}\n\n### Instruction:\n\n{instruction}\n\n### Response:\n"


# ----------------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------------
def _load_model(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            quantization_config=quantization_config,
            trust_remote_code=True,
        )
    except Exception as exc:
        print(f"4-bit quantized load failed ({exc}); retrying without quantization.")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            trust_remote_code=True,
        )
    model.eval()
    return tokenizer, model


def _generate_response(tokenizer, model, prompt, max_new_tokens=1024):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    input_len = inputs["input_ids"].shape[1]
    return tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True).strip()


# ----------------------------------------------------------------------------
# Response processing
# ----------------------------------------------------------------------------
def _extract_code(response):
    """Pull the python code out of the model's response."""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", response, flags=re.DOTALL)
    if blocks:
        code = "\n\n".join(b.strip("\n") for b in blocks)
    else:
        # unterminated fence or plain code
        code = re.sub(r"^```(?:python|py)?\s*\n?", "", response.strip())
        code = code.replace("```", "")
    return code.strip() + "\n"


def _fix_imports(code, ident):
    """
    The model often writes `from your_module import f`. Rewrite any
    `from <module that does not exist> import ...` to import from the real module.
    """
    fixed = []
    for line in code.splitlines():
        m = re.match(r"^(\s*)from\s+([\w.]+)\s+import\s+(.*)$", line)
        if m and m.group(2) != ident:
            module = m.group(2)
            try:
                known = importlib.util.find_spec(module.split(".")[0]) is not None
            except (ImportError, ValueError):
                known = False
            if not known:
                line = f"{m.group(1)}from {ident} import {m.group(3)}"
        fixed.append(line)
    return "\n".join(fixed)


def _trim_to_valid(code):
    """If generation was cut off mid-line, drop trailing lines until the file parses."""
    lines = code.splitlines()
    while lines:
        try:
            ast.parse("\n".join(lines))
            break
        except SyntaxError:
            lines.pop()
    return "\n".join(lines) + "\n"


def _split_asserts(code):
    """
    The model often packs many asserts into ONE test function, so the first wrong assert
    hides all the others. Split each top-level assert (and each `with pytest.raises`)
    into its own test function. Statements before it (setup) are copied along.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    def is_unit(stmt):
        if isinstance(stmt, ast.Assert):
            return True
        if isinstance(stmt, ast.With):
            return any("raises" in ast.unparse(i.context_expr) for i in stmt.items)
        return False

    new_body = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            units = [st for st in node.body if is_unit(st)]
            if len(units) > 1:
                setup, n = [], 0
                for st in node.body:
                    if is_unit(st):
                        n += 1
                        clone = copy.copy(node)
                        clone.name = f"{node.name}_{n}"
                        clone.body = list(setup) + [st]
                        new_body.append(clone)
                    else:
                        setup.append(st)
                continue
        new_body.append(node)
    tree.body = new_body
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def _parse_pytest_summary(stdout):
    """Return (passed, failed) from pytest's last summary line."""
    passed = failed = 0
    for line in reversed(stdout.splitlines()):
        if re.search(r"\b(passed|failed|error|errors)\b", line) and re.search(r" in [\d.]+s", line):
            m = re.search(r"(\d+) passed", line)
            passed = int(m.group(1)) if m else 0
            m = re.search(r"(\d+) failed", line)
            failed = int(m.group(1)) if m else 0
            break
    return passed, failed


def run_tests_and_coverage(entry, response, mode):
    """
    Saves {ID}.py and {ID}_test.py, runs pytest with coverage and returns
    coverage (percent), passed, failed, total_tests. mode: 'vanilla' or 'crafted'.
    """
    ident = _safe_id(entry["task_id"])
    fn = entry["entry_point"]
    os.makedirs(COVERAGE_DIR, exist_ok=True)
    os.makedirs(WORK_DIR, exist_ok=True)

    # {ID}.py : the code under test
    save_file(_program_source(entry), os.path.join(WORK_DIR, f"{ident}.py"))

    # {ID}_test.py : the model's tests, cleaned up, with imports guaranteed
    body = _split_asserts(_trim_to_valid(_fix_imports(_extract_code(response), ident)))
    header = f"import pytest\nfrom {ident} import *\nfrom {ident} import {fn}\n\n"
    test_file = f"{ident}_test.py"
    save_file(header + body, os.path.join(WORK_DIR, test_file))

    cov_path = os.path.join(COVERAGE_DIR, f"{ident}_test_{mode}.json")
    if os.path.exists(cov_path):
        os.remove(cov_path)

    cmd = [
        sys.executable, "-m", "pytest", test_file,
        "-q", "-p", "no:cacheprovider",
        f"--cov={ident}",
        f"--cov-report=json:{cov_path}",
    ]
    # A single test with an infinite loop should only fail itself, not the whole suite.
    if importlib.util.find_spec("pytest_timeout") is not None:
        cmd.append("--timeout=10")
    else:
        print("WARNING: pytest-timeout not installed (pip install pytest-timeout)")

    try:
        proc = subprocess.run(cmd, cwd=WORK_DIR, capture_output=True, text=True, timeout=180)
        stdout = proc.stdout + "\n" + proc.stderr
    except subprocess.TimeoutExpired:
        stdout = "pytest timed out"

    print(stdout[-2000:])
    passed, failed = _parse_pytest_summary(stdout)

    coverage = 0.0
    if os.path.exists(cov_path):
        try:
            with open(cov_path) as f:
                coverage = float(json.load(f)["totals"]["percent_covered"])
        except Exception as exc:
            print(f"Could not read coverage report: {exc}")
    else:
        # make sure a report file still exists for every problem
        with open(cov_path, "w") as f:
            json.dump({"totals": {"percent_covered": 0.0}, "note": "pytest produced no report"}, f)

    return {
        "coverage": coverage,
        "passed": passed,
        "failed": failed,
        "total_tests": passed + failed,
    }


# ----------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------
def prompt_model(dataset, model_name="deepseek-ai/deepseek-coder-6.7b-instruct", vanilla=True, reuse_from=None):
    print(f"Working with {model_name} prompt type {vanilla}...")
    mode = "vanilla" if vanilla else "crafted"

    # Optional: reuse responses already saved in an earlier output file (no model needed)
    cached = {}
    if reuse_from and os.path.exists(reuse_from):
        cached = {r["task_id"]: r for r in read_jsonl(reuse_from)}
        print(f"Reusing {len(cached)} saved responses from {reuse_from}")

    tokenizer = model = None

    results = []
    for entry in dataset:
        if entry["task_id"] in cached:
            prompt = cached[entry["task_id"]]["prompt"]
            response = cached[entry["task_id"]]["response"]
        else:
            if model is None:
                tokenizer, model = _load_model(model_name)
            prompt = build_prompt(entry, vanilla=vanilla)
            response = _generate_response(tokenizer, model, prompt, max_new_tokens=1024)

        stats = run_tests_and_coverage(entry, response, mode)
        coverage = stats["coverage"]

        print(f"Task_ID {entry['task_id']}:\nprompt:\n{prompt}\nresponse:\n{response}\ncoverage:\n{coverage}")
        print(f"tests: total={stats['total_tests']} passed={stats['passed']} failed={stats['failed']}")
        results.append({
            "task_id": entry["task_id"],
            "prompt": prompt,
            "response": response,
            "coverage": coverage,
            "total_tests": stats["total_tests"],
            "passed": stats["passed"],
            "failed": stats["failed"],
        })

    return results


def read_jsonl(file_path):
    dataset = []
    with jsonlines.open(file_path) as reader:
        for line in reader:
            dataset.append(line)
    return dataset


def write_jsonl(results, file_path):
    with jsonlines.open(file_path, "w") as f:
        for item in results:
            f.write_all([item])


if __name__ == "__main__":
    """
    Usage:
    `python3 task_2.py <input_dataset> <model> <output_file> <if_vanilla> [reuse]` 2>&1 | tee prompt.log

    Add the optional 5th argument `reuse` to re-run only the tests/coverage on the
    responses already stored in <output_file> (skips loading and prompting the model).
    """
    args = sys.argv[1:]
    input_dataset = args[0]
    model = args[1]
    output_file = args[2]
    if_vanilla = args[3]  # True or False
    reuse = len(args) > 4 and args[4] == "reuse"

    if not input_dataset.endswith(".jsonl"):
        raise ValueError(f"{input_dataset} should be a `.jsonl` file!")

    if not output_file.endswith(".jsonl"):
        raise ValueError(f"{output_file} should be a `.jsonl` file!")

    vanilla = True if if_vanilla == "True" else False

    dataset = read_jsonl(input_dataset)
    results = prompt_model(dataset, model, vanilla, reuse_from=output_file if reuse else None)
    write_jsonl(results, output_file)
