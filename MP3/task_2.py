import jsonlines
import re
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

#####################################################
# Please finish all TODOs in this file for MP3/task_2;
#####################################################

BASE_SYSTEM_PROMPT = (
    "You are an AI programming assistant. You are an AI programming assistant utilizing "
    "the DeepSeek Coder model, developed by DeepSeek Company, and you only answer "
    "questions related to computer science. For politically sensitive questions, "
    "security and privacy issues, and other non-computer science questions, you will "
    "refuse to answer."
)

FEW_SHOT = '''Here are two worked examples of the expected reasoning.
 
--- Example 1 ---
def sum_even(nums):
    """Return the sum of the even numbers in nums.
    >>> sum_even([1, 2, 3, 4])
    6
    """
    total = 0
    for x in nums:
        if x % 2 == 1:
            total += x
    return total
 
Tests:
assert sum_even([1, 2, 3, 4]) == 6
 
Step 1 (spec): The function must add up only the even numbers.
Step 2 (trace on first test): nums=[1,2,3,4]. x=1: 1%2==1 true, total=1. x=2: 2%2==0, skip. x=3: odd, total=4. x=4: skip. Returns 4.
Step 3 (compare): Expected 6 but the code returns 4. They differ.
Step 4 (inspect): The condition checks x % 2 == 1, which selects odd numbers. It should be x % 2 == 0.
Step 5 (verdict): The traced result contradicts the spec and the test.
<start>Buggy<end>
 
--- Example 2 ---
def largest(nums):
    """Return the largest number in a non-empty list.
    >>> largest([3, 9, 2])
    9
    """
    best = nums[0]
    for x in nums[1:]:
        if x > best:
            best = x
    return best
 
Tests:
assert largest([3, 9, 2]) == 9
 
Step 1 (spec): The function must return the maximum of the list.
Step 2 (trace on first test): best=3. x=9: 9>3, best=9. x=2: 2>9 false. Returns 9.
Step 3 (compare): Expected 9 and the code returns 9. They match.
Step 4 (inspect): Comparison direction, start value and loop range are all correct. Edge case of a single element works because the loop is empty and nums[0] is returned.
Step 5 (verdict): The code matches the spec and the test.
<start>Correct<end>
'''

def save_file(content, file_path):
    with open(file_path, 'w') as file:
        file.write(content)

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

def build_prompt(entry, vanilla=True):
    if vanilla:
        # Mirrors the handout's vanilla prompt: code only, no docstring, generic CoT request.
        code = entry.get("declaration", entry["prompt"]).rstrip() + "\n" + entry["buggy_solution"].rstrip()
        instruction = (
            f"{code}\n\n"
            "Is the above code buggy or correct? Please explain your step by step reasoning. "
            "The prediction should be enclosed within <start> and <end> tags. "
            "For example: <start>Buggy<end>"
        )
    else:
        # Full spec (signature + docstring) so the model knows the intended behavior.
        program = entry["prompt"].rstrip() + "\n" + entry["buggy_solution"].rstrip()
        tests = entry.get("example_test", "").strip()
        instruction = (
            f"{FEW_SHOT}\n"
            "--- Your task ---\n"
            "Decide whether the following implementation correctly satisfies its docstring "
            "and tests. Follow exactly the same five steps as in the examples. Use the real "
            "input values, track every variable, and write out every intermediate calculation. "
            "Do not assume the code is correct or buggy before tracing it.\n\n"
            f"{program}\n\n"
            f"Tests:\n{tests}\n\n"
            "Step 1 (spec): state in one sentence what the docstring requires.\n"
            "Step 2 (trace on first test): execute the code by hand on the first test input.\n"
            "Step 3 (compare): compare the traced result with the expected output.\n"
            "Step 4 (inspect): check operators, comparisons, off-by-one errors, missing logic, "
            "wrong variable or value usage, and edge cases.\n"
            "Step 5 (verdict): the LAST line of your answer must be exactly <start>Buggy<end> "
            "or <start>Correct<end>, with nothing after it."
        )
    return f"{BASE_SYSTEM_PROMPT}\n\n### Instruction:\n\n{instruction}\n\n### Response:\n"

def _generate(tokenizer, model, prompt, max_new_tokens):
    inputs = tokenizer(prompt, return_tensors="pt").to(_model_device(model))
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

def _parse_verdict(response):
    """Return 'buggy', 'correct', or None. Uses the last <start>...<end> tag pair
    (closing tag optional)."""
    matches = re.findall(r"<start>\s*(.*?)\s*(?:<end>|$)", response, flags=re.I | re.S)
    for m in reversed(matches):
        v = m.strip().lower()
        if v.startswith("bug"):
            return "buggy"
        if v.startswith("correct"):
            return "correct"
    return None

def prompt_model(dataset, model_name = "deepseek-ai/deepseek-coder-6.7b-instruct", vanilla = True):
    print(f"Working with {model_name} prompt type {vanilla}...")
 
    tokenizer, model = _load_model(model_name)
    
    # TODO: download the model
    # TODO: load the model with quantization
    
    results = []
    for entry in dataset:
        # TODO: create prompt for the model
        # Tip : Use can use any data from the dataset to create 
        #       the prompt including prompt, canonical_solution, test, etc.
        prompt = build_prompt(entry, vanilla=vanilla)
        
        # TODO: prompt the model and get the response
        response = _generate(tokenizer, model, prompt, 512 if vanilla else 1024)

        # TODO: process the response and save it to results
        verdict = _parse_verdict(response) == "buggy"

        print(f"Task_ID {entry['task_id']}:\nprompt:\n{prompt}\nresponse:\n{response}\nis_expected:\n{verdict}")
        results.append({
            "task_id": entry["task_id"],
            "prompt": prompt,
            "response": response,
            "is_correct": verdict
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
    This Python script is to run prompt LLMs for bug detection.
    Usage:
    `python3 task_2.py <input_dataset> <model> <output_file> <if_vanilla>`|& tee prompt.log

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
    
    dataset = read_jsonl(input_dataset)
    results = prompt_model(dataset, model, vanilla)
    write_jsonl(results, output_file)
