import jsonlines
import os
import re
import subprocess
import sys
import tempfile
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig


DEFAULT_IMPORTS = [
    "java.util.*",
    "java.lang.*",
    "java.util.stream.*",
    "java.util.function.*",
    "java.math.*",
    "java.security.*",
]

OUTCOME_PASS = "True"
OUTCOME_COMPILE = "False (compilation issue)"
OUTCOME_TEST = "False (test failure)"
OUTCOME_TIMEOUT = "False (timeout)"
OUTCOME_NOCODE = "False (no Java code in response)"

## helpers

def load_model(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16, 
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return tokenizer, model

def generate(tokenizer, model, instruction, max_new_tokens=1024):
    """Send `instruction` to DeepSeekCoder using its chat/instruction format and return the response text."""
    if getattr(tokenizer, "chat_template", None):
        messages = [{"role": "user", "content": instruction}]
        input_ids = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        ).to(model.device)
    else:
        # fallback for models without a chat template (e.g. the base model)
        text = f"### Instruction:\n{instruction}\n### Response:\n"
        input_ids = tokenizer(text, return_tensors="pt").input_ids.to(model.device)
 
    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # deterministic so runs are reproducible
            num_return_sequences=1,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(outputs[0][input_ids.shape[1]:], skip_special_tokens=True)

## prompts

def python_source(entry):
    """The Python code to translate: declaration (imports + signature) + canonical solution."""
    return entry["declaration"] + entry["canonical_solution"]
 
 
def java_starter(java_entry):
    """Everything after `class Solution {` in the Java declaration, e.g. the exact method signature."""
    decl = java_entry["declaration"]
    idx = decl.find("class Solution {")
    if idx == -1:
        return decl.strip()
    return decl[idx + len("class Solution {"):].strip("\n")
 
 
def vanilla_prompt(entry):
    return (
        "Can you translate the following Python code into Java?\n"
        "The new Java code must be enclosed between [Java Start] and [Java End]\n\n"
        f"{python_source(entry)}"
    )

EXAMPLE_PY = '''from typing import List
 
 
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                distance = abs(elem - elem2)
                if distance < threshold:
                    return True
 
    return False
'''
 
EXAMPLE_JAVA_SIG = "    public boolean hasCloseElements(List<Double> numbers, double threshold) {"
 
EXAMPLE_JAVA = '''    public boolean hasCloseElements(List<Double> numbers, double threshold) {
        for (int i = 0; i < numbers.size(); i++) {
            for (int j = 0; j < numbers.size(); j++) {
                if (i != j) {
                    double distance = Math.abs(numbers.get(i) - numbers.get(j));
                    if (distance < threshold) {
                        return true;
                    }
                }
            }
        }
        return false;
    }'''


def crafted_prompt(entry, java_entry):
    sig = java_starter(java_entry)
    return f"""You are an expert Python and Java programmer. Translate the Python code below into Java so that it behaves identically on every input.
 
Work through these steps:
1. Plan: in 2-4 short lines, state the input and output types, what the function computes, and any Python-specific behavior that needs care in Java.
2. Write the Java code. It must go inside `class Solution` and use EXACTLY the method signature given (same name, parameter types and return type). Include any helper methods the Python code defines or calls.
3. Check: re-read your Java line by line against the Python for off-by-one errors, loop bounds, and missing logic.

Rules for correct Java:
- Python `//` rounds toward negative infinity and `%` takes the sign of the divisor; Java `/` and `%` truncate toward zero. Use Math.floorDiv / Math.floorMod when negatives are possible.
- Python ints never overflow; use long (or BigInteger) when values can get large.
- Python `round()` rounds half to even; Python slices `a[i:j]`, negative indexes, `sorted`, `set`, `dict`, `zip`, `enumerate` and list comprehensions need explicit Java equivalents (List, Set, Map, loops, streams).
- Use only java.util.*, java.lang.*, java.util.stream.* and java.math.* (the imports are already provided). Do not write import statements, a main method, test code, or a separate class.
- Compare Strings with .equals(), not ==. Return the same type the signature declares (e.g. List<Integer>, not int[]).

The final Java code must be enclosed between [Java Start] and [Java End]. Write the Plan first, then the code between the tags, and put nothing but Java code between the tags.

### Example
Python:
{EXAMPLE_PY}
Java method signature to use:
{EXAMPLE_JAVA_SIG}

Plan: takes a list of doubles and a threshold, returns true if two different elements are closer than the threshold. Python's abs() maps to Math.abs; indexes i != j are compared with nested loops.
[Java Start]
{EXAMPLE_JAVA}
[Java End]

### Your task
Python:
{python_source(entry)}
Java method signature to use (keep it exactly, then complete the body):
{sig}
"""

## java extract and test generation

IMPORT_RE = re.compile(r"^[ \t]*import\s+[\w.*\s]+;[ \t]*$", re.M)
 
 
def extract_java(response):
    """Pull the Java code out of the model response. Returns None if nothing usable is found."""
    candidates = re.findall(r"\[Java Start\](.*?)(?:\[Java End\]|\Z)", response, re.S)
    candidates = [c for c in candidates if "{" in c]
    if candidates:
        code = candidates[-1]
    else:
        # fall back to markdown code fences
        fences = [f for f in re.findall(r"```(?:java)?[ \t]*\n(.*?)```", response, re.S) if "{" in f]
        if not fences:
            return None
        code = fences[-1]
    code = re.sub(r"```(?:java)?", "", code)
    return code.strip("\n")

def build_program(java_entry, code):
    """Combine the model's Java code with the dataset's Java test class into one Main.java."""
    code = re.sub(r"^[ \t]*package\s+[\w.]+;[ \t]*$", "", code, flags=re.M)
 
    # hoist the model's own imports, then remove them from the body
    imports = set(DEFAULT_IMPORTS)
    for line in IMPORT_RE.findall(java_entry["declaration"]):
        imports.add(line.strip()[len("import"):].strip().rstrip(";").strip())
    for line in IMPORT_RE.findall(code):
        imports.add(line.strip()[len("import"):].strip().rstrip(";").strip())
    code = IMPORT_RE.sub("", code)
 
    m = re.search(r"\bclass\s+(\w+)", code)
    if m:
        old = m.group(1)
        if old != "Solution":
            code = re.sub(r"\b%s\b" % re.escape(old), "Solution", code)
        # only Main may be public in Main.java
        code = re.sub(r"\bpublic\s+(final\s+)?class\s+Solution\b", "class Solution", code)
    else:
        code = "class Solution {\n" + code + "\n}"
 
    import_block = "\n".join(f"import {i};" for i in sorted(imports))
    return f"{import_block}\n\n{java_entry['test']}\n\n{code}\n"

def run_java(program, compile_timeout=60, run_timeout=10):
    """Compile and run the program. Returns (outcome, detail)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "Main.java")
        save_file(program, path)
        try:
            comp = subprocess.run(["javac", "Main.java"], cwd=tmp, capture_output=True,
                                  text=True, timeout=compile_timeout)
        except subprocess.TimeoutExpired:
            return OUTCOME_COMPILE, "javac timed out"
        if comp.returncode != 0:
            return OUTCOME_COMPILE, comp.stderr.strip()
        try:
            run = subprocess.run(["java", "-Xmx512m", "Main"], cwd=tmp, capture_output=True,
                                 text=True, timeout=run_timeout)
        except subprocess.TimeoutExpired:
            return OUTCOME_TIMEOUT, f"java run exceeded {run_timeout}s"
        if run.returncode == 0:
            return OUTCOME_PASS, ""
        return OUTCOME_TEST, (run.stderr or run.stdout).strip()
 
 
def evaluate_translation(java_entry, response):
    code = extract_java(response)
    if code is None:
        return OUTCOME_NOCODE, "could not find Java code in the response"
    return run_java(build_program(java_entry, code))

#####################################################
# Please finish all TODOs in this file for MP3/task_1;
#####################################################

def save_file(content, file_path):
    with open(file_path, 'w') as file:
        file.write(content)

def prompt_model(dataset, java_dataset, model_name = "deepseek-ai/deepseek-coder-6.7b-instruct", vanilla = True):
    print(f"Working with {model_name} prompt type {vanilla}...")

    tokenizer, model = load_model(model_name)
 
    java_by_id = {e["task_id"].split("/")[1]: e for e in java_dataset}
    
    # TODO: download the model
    # TODO: load the model with quantization
    
    results = []
    outcomes = []
    for entry in dataset:
        # TODO: create prompt for the model
        # Tip : Use can use any data from the dataset to create 
        #       the prompt including prompt, canonical_solution, test, etc.

        java_entry = java_by_id[entry["task_id"].split("/")[1]]
 
        # create the prompt for the model
        prompt = vanilla_prompt(entry) if vanilla else crafted_prompt(entry, java_entry)
        
        # TODO: prompt the model and get the response
        response = generate(tokenizer, model, prompt, max_new_tokens=1024)

        # TODO: process the response and save it to results
        outcome, detail = evaluate_translation(java_entry, response)
        verdict = (outcome == OUTCOME_PASS)

        print(f"Task_ID {entry['task_id']}:\nprompt:\n{prompt}\nresponse:\n{response}\nis_expected:\n{verdict}")
        print(f"outcome: {outcome}")
        if detail:
            print(f"detail:\n{detail[:1500]}")
        print("-" * 60)
 
        outcomes.append((entry["task_id"], outcome))
        results.append({
            "task_id": entry["task_id"],
            "prompt": prompt,
            "response": response,
            "is_correct": verdict
        })
    

    print("\n===== SUMMARY =====")
    for task_id, outcome in outcomes:
        print(f"{task_id}\t{outcome}")
    n_pass = sum(1 for _, o in outcomes if o == OUTCOME_PASS)
    n_comp = sum(1 for _, o in outcomes if o == OUTCOME_COMPILE)
    n_test = sum(1 for _, o in outcomes if o == OUTCOME_TEST)
    print(f"Passed: {n_pass}/{len(outcomes)} | compilation issues: {n_comp} | test failures: {n_test}")
    print(f"Success rate: {n_pass / len(outcomes):.2%}")
        
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
    This Python script is to run prompt LLMs for code translation.
    Usage:
    `python3 task_1.py <input_dataset> <model> <output_file> <if_vanilla>`|& tee prompt.log

    Inputs:
    - <input_dataset>: A `.jsonl` file, which should be your team's dataset containing 20 HumanEval problems.
    - <model>: Specify the model to use. Options are "deepseek-ai/deepseek-coder-6.7b-base" or "deepseek-ai/deepseek-coder-6.7b-instruct".
    - <output_file>: A `.jsonl` file where the results will be saved.
    - <if_vanilla>: Set to 'True' or 'False' to enable vanilla prompt
    
    Outputs:
    - You can check <output_file> for detailed information.
    """
    args = sys.argv[1:]
    input_dataset = args[0]
    model = args[1]
    output_file = args[2]
    if_vanilla = args[3] # True or False
    
    if not input_dataset.endswith(".jsonl"):
        raise ValueError(f"{input_dataset} should be a `.jsonl` file!")
    
    if not output_file.endswith(".jsonl"):
        raise ValueError(f"{output_file} should be a `.jsonl` file!")
    
    vanilla = True if if_vanilla == "True" else False

    java_dataset_path = os.path.join(
        os.path.dirname(input_dataset),
        os.path.basename(input_dataset).replace("python", "java"),
    )
    if not os.path.exists(java_dataset_path):
        raise FileNotFoundError(f"Expected the Java dataset at {java_dataset_path}")
 
    dataset = read_jsonl(input_dataset)
    java_dataset = read_jsonl(java_dataset_path)
    results = prompt_model(dataset, java_dataset, model, vanilla)
    write_jsonl(results, output_file)
    
