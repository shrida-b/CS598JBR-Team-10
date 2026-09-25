import jsonlines
import sys
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import ast

#####################################################
# Please finish all TODOs in this file for MP1;
# do not change other code/formatting.
#####################################################

def save_file(content, file_path):
    with open(file_path, 'w') as file:
        file.write(content)


def _extract_code_candidate(response: str, entry_point: str = "") -> str:
    """Extract the actual Python code from model output while dropping narrative text."""
    text = response.strip("\n")
    if not text:
        return ""

    # Handle fenced code blocks first.
    code_blocks = re.findall(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if code_blocks:
        text = "\n\n".join(code_blocks)

    if text.startswith("```"):
        text = re.sub(r"^```(?:python)?\s*", "", text, flags=re.IGNORECASE)
    if text.endswith("```"):
        text = re.sub(r"\s*```\s*$", "", text)

    lines = text.splitlines()

    # Skip explanatory preamble before the first real code line.
    start_idx = 0
    while start_idx < len(lines):
        stripped = lines[start_idx].strip()
        if not stripped:
            start_idx += 1
            continue
        if stripped.startswith("```"):
            start_idx += 1
            continue
        if stripped.lower().startswith(("here is", "sure", "certainly", "below is", "the answer is", "code:")):
            start_idx += 1
            continue
        if stripped.startswith(("def ", "class ", "import ", "from ", "return ", "if ", "for ", "while ", "try:", "with ", "@")):
            break
        if stripped.startswith((" ", "\t")) and any(token in stripped for token in ["return ", "if ", "for ", "while ", "try:", "except ", "assert ", "import ", "from ", ":"]):
            break
        if re.match(r"^[A-Za-z][A-Za-z0-9_\s]*:$", stripped) and "def " not in stripped:
            start_idx += 1
            continue
        break

    # Drop tests, demo code, and duplicate problem definitions while preserving
    # helper functions that the generated solution may call.
    kept_lines = []
    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped:
            kept_lines.append(line)
            continue

        if stripped.startswith(("if __name__ ==", "import unittest", ">>>", "doctest.", "<jupyter_")):
            break
        if stripped.startswith(("def main(", "def test_", "class Test")):
            break
        if re.match(r"^def\s+\w+_test\s*\(", stripped):
            break
        if stripped.startswith(("assert ", "print(")) and not line.startswith((" ", "\t")):
            break

        duplicate_entry = entry_point and re.match(rf"^def\s+{re.escape(entry_point)}\s*\(", stripped)
        numbered_duplicate = entry_point and re.match(rf"^def\s+{re.escape(entry_point)}_\d+\s*\(", stripped)
        if duplicate_entry and kept_lines:
            break
        if numbered_duplicate:
            break

        kept_lines.append(line)

    candidate = "\n".join(kept_lines).rstrip()
    return candidate if candidate else text.rstrip()


def prompt_model(dataset, model_name = "deepseek-ai/deepseek-coder-6.7b-base", quantization = True):
    print(f"Working with {model_name} quantization {quantization}...")
    
    # TODO: download the model
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
  
    if quantization:
        # TODO: load the model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map='auto',
            torch_dtype=torch.bfloat16,
            quantization_config=BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type='nf4'
            ),
        )
    else:
        # TODO: load the model without quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True
        )
        

    results = []
    results_processed = []
    for case in dataset:
        prompt = case['prompt']
        
        # TODO: prompt the model and get the response
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        outputs = model.generate(
                **inputs,
                max_new_tokens=500,
                temperature=0.0,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )

        input_len = inputs["input_ids"].shape[1]
        response = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
        
        print(f"Task_ID {case['task_id']}:\nPrompt:\n{prompt}\nResponse:\n{response}")
        results.append(dict(task_id=case["task_id"], completion=response))
        
        # Post-process the generated answer to preserve only executable code.
        # This strips markdown/prose and trims trailing scaffolding or partial
        # output until the completion parses with the HumanEval prompt.
        response_processed = _extract_code_candidate(response, case.get("entry_point", ""))

        candidate_code = response_processed
        for attempt in (candidate_code, response.strip()):
            temp_code = attempt.rstrip("\n")
            while temp_code:
                try:
                    ast.parse(prompt + temp_code)
                    candidate_code = temp_code
                    break
                except SyntaxError:
                    if "\n" in temp_code:
                        temp_code = temp_code.rsplit("\n", 1)[0]
                    else:
                        candidate_code = attempt.rstrip("\n")
                        temp_code = ""

            if candidate_code and candidate_code.strip():
                break

        if not candidate_code or not candidate_code.strip():
            candidate_code = response.rstrip("\n")

        response_processed = candidate_code
        results_processed.append(dict(task_id=case["task_id"], completion=response_processed))
    return results, results_processed

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
    This Python script is to run prompt LLMs for code synthesis.
    Usage:
    `python3 model_prompting.py <input_dataset> <model> <output_file> <output_file_processed> <if_quantization> `|& tee prompt.log

    Inputs:
    - <input_dataset>: A `.jsonl` file, which should be your team's dataset containing 20 HumanEval problems.
    - <model>: Specify the model to use. Options are "deepseek-ai/deepseek-coder-6.7b-base" or "deepseek-ai/deepseek-coder-6.7b-instruct".
    - <output_file>: A `.jsonl` file where the results will be saved.
    - <output_file_processed>: A `.jsonl` file where the processed results will be saved
    - <if_quantization>: Set to 'True' or 'False' to enable or disable model quantization.
    
    Outputs:
    - You can check <output_file> and  <output_file_processed> for detailed information.
    """
    args = sys.argv[1:]
    input_dataset = args[0]
    model = args[1]
    output_file = args[2]
    output_file_processed = args[3]
    if_quantization = args[4] # True or False
    
    if not input_dataset.endswith(".jsonl"):
        raise ValueError(f"{input_dataset} should be a `.jsonl` file!")
    
    if not output_file.endswith(".jsonl"):
        raise ValueError(f"{output_file} should be a `.jsonl` file!")
    
    quantization = True if if_quantization == "True" else False
    
    dataset = read_jsonl(input_dataset)
    results, results_processed = prompt_model(dataset, model, quantization)
    write_jsonl(results, output_file)
    write_jsonl(results_processed, output_file_processed)
