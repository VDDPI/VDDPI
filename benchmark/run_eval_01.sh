#!/bin/bash

########################################
# Configuration
########################################
TRIAL_COUNT=10
SLEEP_TIME=20
VDDPI_DIR=$HOME/VDDPI
VDDPI_BENCH_DIR=$HOME/VDDPI/benchmark
VDDPI_EVAL_DIR=$VDDPI_BENCH_DIR/eval_01.d
APP_ID_FILE=$VDDPI_EVAL_DIR/cache/app_id.txt
REMOTE_RECORD_STATS_SCRIPT=/tmp/record_stats.sh
PROVIDER_DB_CONFIG=$VDDPI_EVAL_DIR/cache/provider_db.cnf
DATA_PROCESSING_CODE="$VDDPI_DIR/docker/gramine_consumer/code_eval_01/main.py"

SKIP_RESTART_REGISTRY=${SKIP_RESTART_REGISTRY:-false}

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
# Initialization
########################################
START_TIME=$(date +%y%m%d-%H%M%S)
rm -f $VDDPI_EVAL_DIR/cache/*

########################################
# Main
########################################
pushd eval_01.d

echo "Starting benchmark for eval_01 at $START_TIME"

echo "=================== Initialization ==================="

if [ "$SKIP_RESTART_REGISTRY" = false ]; then
    echo "Restart containers on registry01.vddpi"
    ssh registry01.vddpi "cd $VDDPI_DIR && \
        make stop-registry > /dev/null 2>&1; \
        make run-registry"
else
    echo "Skipping restart containers on registry01.vddpi"
fi

echo "Restart containers on provider01.vddpi"
ssh provider01.vddpi "cd $VDDPI_DIR && \
    make stop-provider > /dev/null 2>&1; \
    make run-provider"

echo "Setup provider for eval-01"
ssh provider01.vddpi "docker exec -i provider-server bash ./init.sh eval-01 $TRIAL_COUNT"

scp $VDDPI_BENCH_DIR/record_stats.sh registry01.vddpi:$REMOTE_RECORD_STATS_SCRIPT
ssh -T registry01.vddpi "nohup bash $REMOTE_RECORD_STATS_SCRIPT registry-v1-analyzer-1 registry-v1-gramine-1 > /tmp/registry_stats_${START_TIME}.csv 2>&1 & disown"

nohup bash $VDDPI_BENCH_DIR/record_stats.sh gramine-consumer > $VDDPI_EVAL_DIR/result/consumer_stats.csv 2>&1 & disown

echo "Measuring the baseline of stats of containers on registry01.vddpi (waiting for $SLEEP_TIME seconds)."
sleep $SLEEP_TIME

echo "=================== Phase1: Register your data processing app ==================="

./run_phase1.sh "$DATA_PROCESSING_CODE" "$TRIAL_COUNT" "$APP_ID_FILE"

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
./run_phase2.sh "$app_id" "$TRIAL_COUNT" "$PROVIDER_DB_CONFIG" "$VDDPI_EVAL_DIR/cache"

fetch_logs "provider01.vddpi" "provider-server"  "result/eval_obtaining_processing_spec.log"

echo "=================== Phase3: Data processing ==================="

./run_phase3.sh "$VDDPI_DIR" "$VDDPI_BENCH_DIR" "$VDDPI_EVAL_DIR/cache"

echo "=================== Phase4: Data processing (No SGX) ==================="

./run_phase4.sh "$VDDPI_DIR" "$TRIAL_COUNT"
scp consumer01.vddpi:$VDDPI_DIR/consumer_benchmark_nosgx/cache/eval_01/benchmark.log result/eval_data_processing_nosgx.log

echo "=================== Finalization ==================="

echo "Measuring the baseline of stats of containers on registry01.vddpi (waiting for $SLEEP_TIME seconds)."
sleep $SLEEP_TIME
ssh registry01.vddpi "pkill -f $REMOTE_RECORD_STATS_SCRIPT"
pkill -f $VDDPI_BENCH_DIR/record_stats.sh

echo "Fetch stats result from registry01.vddpi"
scp registry01.vddpi:/tmp/registry_stats_${START_TIME}.csv $VDDPI_EVAL_DIR/result/registry_stats.csv
ssh registry01.vddpi "rm -f /tmp/registry_stats_${START_TIME}.csv"

echo "Benchmark finished."

########################################
# Finalization
########################################
END_TIME=$(date +%y%m%d-%H%M%S)
echo "Start time: $START_TIME, End time: $END_TIME"

popd > /dev/null