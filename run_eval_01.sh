#!/bin/bash

mode="eval-01"
trial_count=5
sleep_time=20
app_id_list="./cache/app_id_list.txt"

VDDPI_DIR="~/VDDPI"

start_time=$(date +%y%m%d-%H%M%S)

echo "Restart containers on registry01.vddpi"
ssh -T registry01.vddpi "cd $VDDPI_DIR && \
    make stop-registry && \
    make run-registry"

echo "Restart containers on provider01.vddpi"
ssh -T provider01.vddpi "cd $VDDPI_DIR && \
    make stop-provider && \
    make MODE=eval-01 run-provider"

echo "Start recording stats of containers on registry01.vddpi"
interval=3
ssh -T registry01.vddpi "nohup $VDDPI_DIR/registry/record_stats.sh $interval > /tmp/container_stats-${start_time}.csv 2>&1 & disown"

echo "=================== Phase1: Register your data processing app ==================="

./run_eval_01.d/run_eval_01_phase1.sh "$VDDPI_DIR" "$start_time" "$sleep_time" "$trial_count" "$app_id_list"

echo "=================== Phase2: Apply for data usage ==================="

./run_eval_01.d/run_eval_01_phase2.sh "$app_id_list"

echo "After waiting for $sleep_time seconds, stop recording stats of containers on registry01.vddpi"
sleep $sleep_time
ssh -T registry01.vddpi "pkill -f record_stats.sh"

echo "Fetch stats result from registry01.vddpi"
scp registry01.vddpi:/tmp/container_stats-${start_time}.csv run_eval_01.d/result/container_stats.csv
