#!/bin/bash

vddpi_dir="$1"
start_time="$2"
sleep_time="$3"
trial_count="$4"
app_id_list="$5"

file="docker/gramine_consumer/code_eval_01/main.py"
./run_eval_01.d/eval_app_registration.sh "$file" "$trial_count" "$app_id_list"

./run_eval_01.d/eval_obtaining_app_id.sh

./run_eval_01.d/eval_code_analysis.sh