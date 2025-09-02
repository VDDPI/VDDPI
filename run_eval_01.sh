#!/bin/bash

mode="eval-01"

echo "=================== Phase1: Register your data processing app ==================="
echo "Please start the registry (\$make run-registry)."
echo ""
read -p "If the registry is running, press Enter to continue..."

file="docker/gramine_consumer/code_eval_01/main.py"
./run_eval_01.d/eval_app_registration.sh "$file" 5
