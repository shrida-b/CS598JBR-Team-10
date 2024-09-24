###################################################################
# This is a list of all commands you need to run for MP2 on Colab.
###################################################################

# TODO: Clone your GitHub repository
! git clone [Your GitHub Link]
%cd [Your GitHub Repo]

# TODO: Replace the file path of selected_humaneval_[seed].jsonl generated in MP1
input_dataset = ""# selected_humaneval_[seed].jsonl

# Set up requirements for model prompting
! bash -x MP2/setup_models.sh

# TODO: add your seed generated in MP1
seed = "<your_seed>"
task_1_vanilla_json = "task_1" + seed + "_vanilla.jsonl"
task_1_json = "task_1_" + seed + "_prompting.jsonl"
task_2_vanilla_json = "task_2" + seed + "_vanilla.jsonl"
task_2_json = "task_2_" + seed + "_prompting.jsonl"

# Prompt the models, you can create your `MP2/task_1.py, MP2/task_2.py` by modifying `MP2/task_[ID].py` 
# The {input_dataset} is the JSON file consisting of 20 unique programs for your group that you generated in MP1 (selected_humaneval_[seed].jsonl)
! python3 MP2/task_1.py {input_dataset} "deepseek-ai/deepseek-coder-6.7b-instruct" {task_1_vanilla_json} "True" |& tee Task_1_vanilla.log
! python3 MP2/task_1.py {input_dataset} "deepseek-ai/deepseek-coder-6.7b-instruct" {task_1_json} "True" |& tee Task_1_prompting.log 
! python3 MP2/task_2.py {input_dataset} "deepseek-ai/deepseek-coder-6.7b-instruct" {task_2_vanilla_json} "True" |& tee Task_2_vanilla.log
! python3 MP2/task_2.py {input_dataset} "deepseek-ai/deepseek-coder-6.7b-instruct" {task_2_json} "True" |& tee Task_2_prompting.log

%cd ..

# git push all nessacery files (e.g., *jsonl, *log) to your GitHub repository
