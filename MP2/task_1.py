import ast
import hashlib
import json
import os
import random
import re
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

#####################################################
# Please finish all TODOs in this file for MP2;
#####################################################


BASE_SYSTEM_PROMPT = (
    "You are an AI programming assistant. You are an AI programming assistant, "
    "utilizing the DeepSeek Coder model, developed by DeepSeek Company, and you "
    "only answer questions related to computer science. For politically sensitive "
    "questions, security and privacy issues, and other non-computer science "
    "questions, you will refuse to answer."
)


def save_file(content, file_path):
    with open(file_path, "w") as file:
        file.write(content)


def _json_default(value):
    if isinstance(value, tuple):
        return list(value)
    return repr(value)


def _jsonl_loads(line):
    return json.loads(line)


def _jsonl_dumps(item):
    return json.dumps(item, default=_json_default, ensure_ascii=False)


def _literal_or_source(source):
    try:
        return ast.literal_eval(source)
    except Exception:
        return source


def _normalize_for_compare(value):
    if isinstance(value, float):
        return round(value, 12)
    if isinstance(value, tuple):
        return tuple(_normalize_for_compare(item) for item in value)
    if isinstance(value, list):
        return [_normalize_for_compare(item) for item in value]
    if isinstance(value, dict):
        return {
            _normalize_for_compare(key): _normalize_for_compare(val)
            for key, val in value.items()
        }
    return value


def _parse_model_output(response):
    """Return the value enclosed in [Output] tags when it can be parsed."""
    # match = re.search(
    #     r"\[Output\](.*?)\[(?:/|\\)Output\]",
    #     response,
    #     flags=re.IGNORECASE | re.DOTALL,
    # )
    # text = match.group(1).strip() if match else response.strip()
    # text = text.strip("` \n\t")

    matches = re.findall(
        r"\[Output\](.*?)(?:\[(?:/|\\)Output\]|$)",
        response,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = (matches[-1] if matches else response).strip()
    text = text.strip("` \n\t")

    # If the model included a sentence inside the tag, keep the last plausible
    # literal-like line. This keeps grading robust without rewarding prose.
    candidates = [text]
    candidates.extend(line.strip() for line in text.splitlines() if line.strip())
    for candidate in reversed(candidates):
        cleaned = candidate.rstrip(".")
        try:
            return ast.literal_eval(cleaned)
        except Exception:
            if cleaned in {"True", "False", "None"}:
                return {"True": True, "False": False, "None": None}[cleaned]
    return text


def _prediction_is_correct(response, expected):
    predicted = _parse_model_output(response)
    return _normalize_for_compare(predicted) == _normalize_for_compare(expected)


def _call_expr_from_assert(assert_node):
    """Extract candidate(...) and expected value from supported assert shapes."""
    test = assert_node.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return None
    if not isinstance(test.ops[0], (ast.Eq, ast.Is)):
        return None

    left = test.left
    right = test.comparators[0]
    if isinstance(left, ast.Call) and isinstance(left.func, ast.Name) and left.func.id == "candidate":
        return left, right
    if isinstance(right, ast.Call) and isinstance(right.func, ast.Name) and right.func.id == "candidate":
        return right, left
    return None


def _extract_candidate_assertions(entry):
    assertions = []
    test_source = entry["test"]
    try:
        module = ast.parse(test_source)
    except SyntaxError:
        return assertions

    for node in ast.walk(module):
        if not isinstance(node, ast.Assert):
            continue
        extracted = _call_expr_from_assert(node)
        if not extracted:
            continue
        call_node, expected_node = extracted
        call_source = ast.get_source_segment(test_source, call_node) or ""
        expected_source = ast.get_source_segment(test_source, expected_node) or ""
        if not call_source or not expected_source:
            continue
        input_source = call_source[len("candidate") :].strip()
        assertions.append(
            {
                "call": call_source,
                "inputs": input_source,
                "expected_source": expected_source,
                "expected": _literal_or_source(expected_source),
            }
        )
    return assertions


def _format_call_inputs(args, kwargs):
    parts = [repr(arg) for arg in args]
    parts.extend(f"{key}={value!r}" for key, value in kwargs.items())
    return "(" + ", ".join(parts) + ")"


def _execute_candidate_calls(entry):
    namespace = {}
    exec(_program_source(entry), namespace)
    exec(entry["test"], namespace)
    target = namespace[entry["entry_point"]]
    check = namespace["check"]
    calls = []

    def recording_candidate(*args, **kwargs):
        result = target(*args, **kwargs)
        calls.append(
            {
                "call": "candidate" + _format_call_inputs(args, kwargs),
                "inputs": _format_call_inputs(args, kwargs),
                "expected_source": repr(result),
                "expected": result,
            }
        )
        return result

    check(recording_candidate)
    return calls


def _stable_index(task_id, count):
    seed_material = os.environ.get("MP2_TASK1_ASSERTION_SEED", "0") + ":" + task_id
    digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
    return int(digest, 16) % count


def _select_assertion(entry):
    assertions = _extract_candidate_assertions(entry)
    if not assertions:
        assertions = _execute_candidate_calls(entry)
    if not assertions:
        raise ValueError(f"No supported candidate(...) == expected assertion found for {entry['task_id']}")
    return assertions[_stable_index(entry["task_id"], len(assertions))]


def _program_source(entry):
    return entry["prompt"].rstrip() + "\n" + entry["canonical_solution"].rstrip() + "\n"


def _function_signature(entry):
    try:
        module = ast.parse(entry["prompt"])
    except SyntaxError:
        return entry.get("entry_point", "the function")
    for node in module.body:
        if isinstance(node, ast.FunctionDef):
            if node.name != entry.get("entry_point"):
                continue
            args = [arg.arg for arg in node.args.args]
            return f"{node.name}({', '.join(args)})"
    return entry.get("entry_point", "the function")


def build_prompt(entry, vanilla=True):
    selected = _select_assertion(entry)
    program = _program_source(entry)
    function_call = entry["entry_point"] + selected["inputs"]

    if vanilla:
        instruction = (
            f"If the input is {selected['inputs']}, what will the following code return?\n\n"
            "The return value prediction must be enclosed between [Output] and [/Output] tags. "
            "For example : [Output]prediction[/Output].\n\n"
            f"{program}"
        )
    else:
        signature = _function_signature(entry)
        instruction = (
            f"Predict the exact return value of this Python call: {function_call}\n\n"
            "Work through the code like an interpreter. Track every variable's value after each "
            "loop iteration or branch, write out every intermediate calculation explicitly, and "
            "double-check arithmetic, indexing, string lengths, and comparisons. Use the actual "
            "input values, not the docstring examples.\n"
            "After your reasoning, the LAST line of your response must be exactly of the form "
            "[Output]value[/Output], where value is a Python literal (strings in quotes, tuples in "
            "parentheses, lists in brackets). Write nothing after that line.\n\n"
            "Example:\n"
            "def f(xs):\n    t = 0\n    for i, x in enumerate(xs):\n        if i % 2 == 0:\n            t += x\n    return t\n"
            "Call: f([4, 5, 6])\n"
            "Trace: i=0, x=4, even index, t=0+4=4. i=1, x=5, odd index, skip. "
            "i=2, x=6, even index, t=4+6=10. Loop ends.\n"
            "[Output]10[/Output]\n\n"
            f"Now do the same for the real task.\nCall: {function_call}\n\n{program}"
        )

    prompt = f"{BASE_SYSTEM_PROMPT}\n\n### Instruction:\n\n{instruction}\n\n### Response:\n"
    return prompt, selected


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


def _model_device(model):
    if hasattr(model, "device"):
        return model.device
    return next(model.parameters()).device


def _generate_response(tokenizer, model, prompt, vanilla):
    inputs = tokenizer(prompt, return_tensors="pt").to(_model_device(model))
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128 if vanilla else 700,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    input_len = inputs["input_ids"].shape[1]
    return tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True).strip()


def prompt_model(dataset, model_name = "deepseek-ai/deepseek-coder-6.7b-instruct", vanilla = True):
    print(f"Working with {model_name} prompt type {vanilla}...")

    # TODO: download the model
    # TODO: load the model with quantization
    tokenizer, model = _load_model(model_name)

    results = []
    for entry in dataset:
        # TODO: create prompt for the model
        # Tip : Use can use any data from the dataset to create
        #       the prompt including prompt, canonical_solution, test, etc.
        prompt, selected = build_prompt(entry, vanilla=vanilla)

        # TODO: prompt the model and get the response
        response = _generate_response(tokenizer, model, prompt, vanilla=vanilla)

        # TODO: process the response and save it to results
        verdict = _prediction_is_correct(response, selected["expected"])

        print(
            f"Task_ID {entry['task_id']}:\n"
            f"selected_test: {selected['call']} == {selected['expected_source']}\n"
            f"prompt:\n{prompt}\nresponse:\n{response}\nis_correct:\n{verdict}"
        )
        results.append(
            {
                "task_id": entry["task_id"],
                "prompt": prompt,
                "response": response,
                "is_correct": verdict,
            }
        )

    return results


def read_jsonl(file_path):
    dataset = []
    with open(file_path, "r", encoding="utf-8") as reader:
        for line in reader:
            if line.strip():
                dataset.append(_jsonl_loads(line))
    return dataset


def write_jsonl(results, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        for item in results:
            f.write(_jsonl_dumps(item) + "\n")


if __name__ == "__main__":
    """
    This Python script is to run prompt LLMs for code execution reasoning.
    Usage:
    `python3 task_1.py <input_dataset> <model> <output_file> <if_vanilla>` |& tee prompt.log

    Inputs:
    - <input_dataset>: A `.jsonl` file, which should be your team's dataset containing 20 HumanEval problems.
    - <model>: Specify the model to use. Options are "deepseek-ai/deepseek-coder-6.7b-base" or "deepseek-ai/deepseek-coder-6.7b-instruct".
    - <output_file>: A `.jsonl` file where the results will be saved.
    - <if_vanilla>: Set to 'True' or 'False' to enable vanilla prompt.

    Outputs:
    - You can check <output_file> for detailed information.
    """
    args = sys.argv[1:]
    if len(args) != 4:
        raise ValueError(
            "Usage: python3 task_1.py <input_dataset> <model> <output_file> <if_vanilla>"
        )

    input_dataset = args[0]
    model = args[1]
    output_file = args[2]
    if_vanilla = args[3]

    if not input_dataset.endswith(".jsonl"):
        raise ValueError(f"{input_dataset} should be a `.jsonl` file!")

    if not output_file.endswith(".jsonl"):
        raise ValueError(f"{output_file} should be a `.jsonl` file!")

    vanilla = True if if_vanilla == "True" else False

    random.seed(os.environ.get("MP2_TASK1_ASSERTION_SEED", "0"))
    dataset = read_jsonl(input_dataset)
    results = prompt_model(dataset, model, vanilla)
    write_jsonl(results, output_file)
