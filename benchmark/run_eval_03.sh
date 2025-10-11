#!/bin/bash

########################################
# Configuration
########################################
TRIAL_COUNT=1
PARALLEL_NUM=2
SLEEP_TIME=20
VDDPI_DIR=$HOME/VDDPI
VDDPI_BENCH_DIR=$HOME/VDDPI/benchmark
VDDPI_EVAL_DIR=$VDDPI_BENCH_DIR/eval_03.d
APP_ID_FILE=$VDDPI_EVAL_DIR/cache/app_id.txt
REMOTE_RECORD_STATS_SCRIPT=/tmp/record_stats.sh
PROVIDER_DB_CONFIG=$VDDPI_EVAL_DIR/cache/provider_db.cnf
DATA_PROCESSING_CODE="$VDDPI_DIR/docker/gramine_consumer/code_eval_03/main.py"

PATH_RUN_LOG="$VDDPI_EVAL_DIR/result/run.log"

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

write_log() {
    while IFS= read -r message; do
        echo "[$(date '+%Y-%m-%d %H:%M:%S.%3N')] $message" | tee -a "$PATH_RUN_LOG"
    done
}

########################################
# Initialization
########################################
START_TIME=$(date +%y%m%d-%H%M%S)
rm -f $VDDPI_EVAL_DIR/cache/*
rm -f $VDDPI_EVAL_DIR/result/*

########################################
# Main
########################################
pushd eval_03.d

echo "Starting benchmark for eval_03 at $START_TIME" | write_log

echo "=================== Initialization ===================" | write_log

if [ "$SKIP_RESTART_REGISTRY" = false ]; then
    echo "Restart containers on registry01.vddpi" | write_log
    ssh registry01.vddpi "cd $VDDPI_DIR && \
        make stop-registry > /dev/null 2>&1; \
        make run-registry"
else
    echo "Skipping restart containers on registry01.vddpi" | write_log
fi

echo "Restart containers on provider01.vddpi" | write_log
ssh provider01.vddpi "cd $VDDPI_DIR && \
    make stop-provider > /dev/null 2>&1; \
    make run-provider"

echo "Setup provider for eval-03" | write_log
ssh provider01.vddpi "docker exec -i provider-server bash ./init.sh eval-03 $TRIAL_COUNT"

scp $VDDPI_BENCH_DIR/record_stats.sh registry01.vddpi:$REMOTE_RECORD_STATS_SCRIPT
ssh -T registry01.vddpi "nohup bash $REMOTE_RECORD_STATS_SCRIPT registry-v1-analyzer-1 registry-v1-gramine-1 > /tmp/registry_stats_${START_TIME}.csv 2>&1 & disown"

bash $VDDPI_BENCH_DIR/record_stats.sh gramine-consumer > $VDDPI_EVAL_DIR/result/consumer_container_stats.csv 2>/dev/null &

dool --time --cpu --mem --net --disk --nocolor --noheaders --ascii --output=$VDDPI_EVAL_DIR/result/consumer_host_stats.csv $INTERVAL 2>/dev/null &

echo "Measuring the baseline of stats of containers on registry01.vddpi (waiting for $SLEEP_TIME seconds)." | write_log
sleep $SLEEP_TIME

echo "=================== Phase1: Register your data processing app ===================" | write_log

./run_phase1.sh "$DATA_PROCESSING_CODE" "$APP_ID_FILE" | write_log

# Fetch logs
fetch_logs "registry01.vddpi" "registry-v1-gramine-1"  "result/eval_obtaining_app_id.log"
fetch_logs "registry01.vddpi" "registry-v1-analyzer-1" "result/eval_code_analysis.log"

echo "=================== Phase2: Apply for data usage ===================" | write_log

app_id=$(cat $APP_ID_FILE)
cat > $PROVIDER_DB_CONFIG <<- EOF
    [client]
    user=root
    password=root
    host=provider01.vddpi
EOF
./run_phase2.sh "$app_id" "$TRIAL_COUNT" "$PROVIDER_DB_CONFIG" "$VDDPI_EVAL_DIR/cache" | write_log

fetch_logs "provider01.vddpi" "provider-server"  "result/eval_obtaining_processing_spec.log"

echo "=================== Phase3: Data processing ===================" | write_log

rm -f $VDDPI_DIR/consumer/cache/*
rm -f $VDDPI_DIR/consumer/certs/*
rm -f $VDDPI_DIR/consumer/logs/*

phase3_pids=()

for i in $(seq 1 $PARALLEL_NUM)
do
    consumer_dir_name="consumer_$i"
    (
        cd $VDDPI_DIR
        ./x_copy_consumer.sh "$i"
        ls $consumer_dir_name/certs | write_log
    )
    echo "Starting data processing in parallel (instance:$i, consumer_dir_name:$consumer_dir_name)" | write_log
    ./run_phase3.sh "$VDDPI_DIR" "$VDDPI_BENCH_DIR" "$consumer_dir_name" "$VDDPI_EVAL_DIR/cache" | write_log &
    phase3_pids+=($!)
done

echo "Starting data processing in parallel (consumer_dir_name:consumer)" | write_log
./run_phase3.sh "$VDDPI_DIR" "$VDDPI_BENCH_DIR" "consumer" "$VDDPI_EVAL_DIR/cache" | write_log &
phase3_pids+=($!)

echo "Waiting for all data processing to complete..." | write_log
for pid in "${phase3_pids[@]}"; do
    wait "$pid"
done
echo "All data processing completed." | write_log

echo "=================== Finalization ===================" | write_log

echo "Measuring the baseline of stats of containers on registry01.vddpi (waiting for $SLEEP_TIME seconds)." | write_log
sleep $SLEEP_TIME

pkill dool

ssh registry01.vddpi "pkill -f $REMOTE_RECORD_STATS_SCRIPT"
pkill -f $VDDPI_BENCH_DIR/record_stats.sh

echo "Fetch stats result from registry01.vddpi" | write_log
scp registry01.vddpi:/tmp/registry_stats_${START_TIME}.csv $VDDPI_EVAL_DIR/result/registry_stats.csv
ssh registry01.vddpi "rm -f /tmp/registry_stats_${START_TIME}.csv"

echo "Benchmark finished." | write_log

########################################
# Finalization
########################################
END_TIME=$(date +%y%m%d-%H%M%S)
echo "Finish $0: (start:$START_TIME, end:$END_TIME)" | write_log

popd > /dev/null
