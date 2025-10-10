#!/bin/bash

########################################
# Configuration
########################################
LOGFILE="result/eval_data_processing.log"

########################################
# Arguments
########################################
vddpi_dir="$1"
vddpi_bench_dir="$2"
consumer_dir_name="$3"
container_name="$4"
cache_dir="$5"
manage_port="$6"
app_port="$7"

########################################
# Initialization
########################################
> "$LOGFILE"

########################################
# Main
########################################

echo "Restart containers on consumer01.vddpi"
(
    cd $vddpi_dir
    EXPERIMENT_CONTAINER_NAME=$container_name make stop-consumer > /dev/null 2>&1
    echo "MODE=eval-03 CONSUMER_DIR_NAME=$consumer_dir_name EXPERIMENT_CONTAINER_NAME=$container_name make run-consumer"
    MODE=eval-03 CONSUMER_DIR_NAME=$consumer_dir_name EXPERIMENT_CONTAINER_NAME=$container_name make run-consumer
)

# The first loop iteration retrieves data from the provider; the second iteration uses that data as cache.
echo "Run gencert"
python3 $vddpi_bench_dir/client.py gencert "$cache_dir" "consumer01.vddpi" 8001

echo "Run processing data"
for token in $cache_dir/token-*
do
    start_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
    start_epoch=$(date +%s%3N)

    msg=$(python3 $vddpi_bench_dir/client.py process "$token" "$cache_dir" "consumer01.vddpi" 8002)

    end_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
    end_epoch=$(date +%s%3N)
    duration=$((end_epoch - start_epoch))

    echo "$msg" | head -n 1
    log=$(echo "$msg" | grep "Session completed" | sed -n 's/.*(\(.*\)).*/\1/p')
    echo "___BENCH___ Data processing (start_total:$start_ts, end_total:$end_ts, duration_total_ms:$duration, $log)" >> "$LOGFILE"
done
