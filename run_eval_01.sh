#!/bin/bash

mode="eval-01"
trial_count=5
sleep_time=20

VDDPI_DIR="~/VDDPI"

start_time=$(date +%y%m%d-%H%M%S)

echo "=================== Phase1: Register your data processing app ==================="
echo "Please start the registry (\$make run-registry)."
echo ""
read -p "If the registry is running, press Enter to continue..."

echo "Restart containers on registry01.vddpi"
ssh -T registry01.vddpi "cd $VDDPI_DIR/registry && \
    docker compose down && \
    docker compose up -d"

echo "Start recording stats of containers on registry01.vddpi"
interval=3
ssh -T registry01.vddpi "nohup $VDDPI_DIR/registry/record_stats.sh $interval > /tmp/container_stats-${start_time}.csv 2>&1 & disown"

echo "Waiting for $sleep_time seconds..."
sleep $sleep_time

file="docker/gramine_consumer/code_eval_01/main.py"
app_list="./cache/app_id_list.txt"
./run_eval_01.d/eval_app_registration.sh "$file" "$trial_count" "$app_list"

./run_eval_01.d/eval_obtaining_app_id.sh

./run_eval_01.d/eval_code_analysis.sh

echo "Waiting for $sleep_time seconds..."
sleep $sleep_time

echo "Stop recording stats of containers on registry01.vddpi"
ssh -T registry01.vddpi "pkill -f record_stats.sh"

echo "Fetch stats result from registry01.vddpi"
scp registry01.vddpi:/tmp/container_stats-${start_time}.csv run_eval_01.d/result/container_stats.csv