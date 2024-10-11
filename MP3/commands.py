###################################################################
# This is a list of all commands you need to run for MP3 on Colab.
###################################################################

# TODO: Clone your GitHub repository
! git clone [Your GitHub Link]
%cd [Your GitHub Repo]/MP3

# TODO: MP1 `selected_humaneval_[seed].jsonl` dataset path
MP1_Dataset = ""

# Set up requirements for dataset generation
! bash -x setup_dataset.sh

# dataset generation
! python3 humanevalx_dataset_generation.py [MP1_Dataset] |& tee humanevalx_dataset_generation.log

seed = "[your_seed]"
# TODO: Replace the file path of selected_codenet_[seed].jsonl generated in previous step
input_python_dataset = "selected_humanevalx_python_" + seed + ".jsonl"
input_java_dataset = "selected_humanevalx_java_" + seed + ".jsonl"

# Set up requirements for model prompting
! bash -x setup_models.sh

task_1_vanilla_jsonl = "task_1_" + seed + "_vanilla.jsonl"
task_1_crafted_jsonl = "task_1_" + seed + "_crafted.jsonl"

# Task 1
! python3 task_1.py {input_python_dataset} {task_1_vanilla_jsonl} |& tee task_1_vanilla.log
! python3 task_1.py {input_python_dataset} {task_1_crafted_jsonl} |& tee task_1_crafted.log

# Task 2

humaneval_input_dataset = "selected_humaneval_" + seed + ".jsonl"

# Prompt the models, you can modify `MP3/task_2.py`
# The {input_dataset} is the JSON file consisting of 20 unique programs for your group that you generated in MP1 (selected_humaneval_[seed].jsonl)
! python3 humanevalpack_dataset_generation.py {humaneval_input_dataset} |& tee humanevalpack_dataset_generation.log

task_2_vanilla_json = "task_2_" + seed + "_vanilla.jsonl"
task_2_crafted_json = "task_2_" + seed + "_crafted.jsonl"
humanevalpack_input_dataset = "selected_humanevalpack_" + seed + ".jsonl"

! python3 task_2.py {input_dataset} "deepseek-ai/deepseek-coder-6.7b-instruct" {task_2_vanilla_json} "True" |& tee task_2_vanilla.log
! python3 task_2.py {input_dataset} "deepseek-ai/deepseek-coder-6.7b-instruct" {task_2_crafted_json} "False" |& tee task_2_crafted.log

%cd ..

# git push all nessacery files (e.g., *jsonl, *log) to your GitHub repository
