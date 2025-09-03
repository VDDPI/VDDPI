#!/bin/bash

########################################
# Configuration
########################################
TRIAL_COUNT=5
SLEEP_TIME=20
VDDPI_DIR=$HOME/VDDPI
VDDPI_BENCH_DIR=$HOME/VDDPI/benchmark
VDDPI_EVAL_DIR=$VDDPI_BENCH_DIR/eval_01.d
APP_ID_FILE=$VDDPI_EVAL_DIR/cache/app_id.txt
START_TIME=$(date +%y%m%d-%H%M%S)
REMOTE_RECORD_STATS_SCRIPT=/tmp/record_stats.sh
PROVIDER_DB_CONFIG=$VDDPI_EVAL_DIR/cache/provider_db.cnf

########################################
# Functions
########################################
fetch_logs() {
    local hostname="$1"
    local container_name="$2"
    local log_file="$3"
    ssh -T "$hostname" "docker logs $container_name" 2>&1 | grep "___BENCH___" > "$log_file"
}

########################################
# Main
########################################
pushd eval_01.d

echo "Starting benchmark for eval_01 at $START_TIME"

echo "=================== Initialization ==================="

echo "Restart containers on registry01.vddpi"
ssh registry01.vddpi "cd $VDDPI_DIR && \
    make stop-registry > /dev/null 2>&1; \
    make run-registry"

echo "Restart containers on provider01.vddpi"
ssh provider01.vddpi "cd $VDDPI_DIR && \
    make stop-provider > /dev/null 2>&1; \
    make run-provider"

echo "Setup provider for eval-01"
ssh provider01.vddpi "docker exec -i provider-server bash ./init.sh eval-01"

echo "After waiting for $SLEEP_TIME seconds, start recording stats of containers on registry01.vddpi"
sleep $SLEEP_TIME
scp $VDDPI_BENCH_DIR/record_stats.sh registry01.vddpi:$REMOTE_RECORD_STATS_SCRIPT
ssh -T registry01.vddpi "nohup bash $REMOTE_RECORD_STATS_SCRIPT > /tmp/container_stats_${START_TIME}.csv 2>&1 & disown"

echo "=================== Phase1: Register your data processing app ==================="

VDDPI_DIR=$VDDPI_DIR ./run_phase1.sh "$TRIAL_COUNT" "$APP_ID_FILE" "result/eval_app_registration.log"

# Fetch logs
fetch_logs "registry01.vddpi" "registry-v1-gramine-1"  "result/eval_obtaining_app_id.log"
fetch_logs "registry01.vddpi" "registry-v1-analyzer-1" "result/eval_code_analysis.log"

echo "=================== Phase2: Apply for data usage ==================="

app_id=$(cat $APP_ID_FILE)
cat > $PROVIDER_DB_CONFIG <<- EOF
    [client]
    user=root
    password=root
    host=provider01.vddpi
EOF
./run_phase2.sh "$app_id" "$TRIAL_COUNT" "$PROVIDER_DB_CONFIG"

fetch_logs "provider01.vddpi" "provider-server"  "result/eval_obtaining_processing_spec.log"

echo "=================== Finalization ==================="

echo "After waiting for $SLEEP_TIME seconds, stop recording stats of containers on registry01.vddpi"
sleep $SLEEP_TIME
ssh registry01.vddpi "pkill -f $REMOTE_RECORD_STATS_SCRIPT"

echo "Fetch stats result from registry01.vddpi"
scp registry01.vddpi:/tmp/container_stats_${START_TIME}.csv ./result/container_stats.csv
ssh registry01.vddpi "rm -f /tmp/container_stats_${START_TIME}.csv"

echo "Benchmark finished."
popd