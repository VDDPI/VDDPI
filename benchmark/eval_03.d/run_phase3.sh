#!/bin/bash

########################################
# Arguments
########################################
vddpi_dir="$1"
vddpi_bench_dir="$2"
consumer_dir_name="$3"
cache_dir="$4"

########################################
# Initialization
########################################
LOGFILE="result/eval_data_processing-${consumer_dir_name}.log"
LOGFILE_TMP="result/tmp-${consumer_dir_name}.log"
> "$LOGFILE"

########################################
# Main
########################################

echo "Restart the container ($container_dir_name) on consumer01.vddpi" | tee -a $LOGFILE_TMP
(
    cd $vddpi_dir
    CONSUMER_DIR_NAME=$consumer_dir_name make stop-consumer > /dev/null 2>&1
    MODE=eval-03 CONSUMER_DIR_NAME=$consumer_dir_name make run-consumer
)

set -a
source $vddpi_dir/$consumer_dir_name/.env
set +a

# The first loop iteration retrieves data from the provider; the second iteration uses that data as cache.
echo "Run gencert (port:$CONSUMER_MANAGE_PORT)" | tee -a $LOGFILE_TMP
python3 $vddpi_bench_dir/client.py gencert "$cache_dir" "consumer01.vddpi" $CONSUMER_MANAGE_PORT | tee -a $LOGFILE_TMP

echo "Run processing data (port:$CONSUMER_APP_PORT)" | tee -a $LOGFILE_TMP
for token in $cache_dir/token-*
do
    start_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
    start_epoch=$(date +%s%3N)

    msg=$(python3 $vddpi_bench_dir/client.py process "$token" "$cache_dir" "consumer01.vddpi" $CONSUMER_APP_PORT | tee -a $LOGFILE_TMP)

    end_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
    end_epoch=$(date +%s%3N)
    duration=$((end_epoch - start_epoch))

    echo "$msg" | grep "Received:"
    log=$(echo "$msg" | grep "Session completed" | sed -n 's/.*(\(.*\)).*/\1/p')
    echo "___BENCH___ Data processing (start_total:$start_ts, end_total:$end_ts, duration_total_ms:$duration, $log)" >> "$LOGFILE"
done
