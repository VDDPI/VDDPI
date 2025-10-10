#!/bin/bash

########################################
# Arguments
########################################
vddpi_dir="$1"
vddpi_bench_dir="$2"
cache_dir="$3"
parallel_index="$4"

if [ "$parallel_index" -gt 0 ]; then
    exit 1
fi

########################################
# Configuration
########################################
LOGFILE="result/eval_data_processing-$parallel_index.log"
MANAGE_PORT=$((10#${parallel_index}8001))
APP_PORT=$((10#${parallel_index}8002))

########################################
# Initialization
########################################
> "$LOGFILE"
source $vddpi_dir/env

########################################
# Functions
########################################
run_consumer() {
    local parallel_index="$1"
    local vddpi_dir="$2"
    consumer_name="consumer"
    if [ "$parallel_index" -gt 0 ]; then
        consumer_name="$consumer_name-$parallel_index"
    fi
    (
        cd $vddpi_dir/$consumer_name
        CONTAINER_NAME=$consumer_name \
        SPID=${SPID} \
        IS_LINKABLE=${IS_LINKABLE} \
        PRIVATE_CA=${PRIVATE_CA} \
        IAS_SUBSCRIPTION_KEY=${IAS_SUBSCRIPTION_KEY} \
        COUNTRY=${COUNTRY_CONSUMER} \
        CNAME=${CNAME_CONSUMER} \
        CONSUMER_HOST_NAME=${CNAME_CONSUMER} \
        docker compose up -d
    )
}

stop_consumer() {
    local parallel_index="$1"
    local vddpi_dir="$2"
    consumer_name="consumer"
    if [ "$parallel_index" -gt 0 ]; then
        consumer_name="$consumer_name-$parallel_index"
    fi
    (
        cd $vddpi_dir/$consumer_name
        CONTAINER_NAME=$consumer_name \
        SPID=${SPID} \
        IS_LINKABLE=${IS_LINKABLE} \
        PRIVATE_CA=${PRIVATE_CA} \
        IAS_SUBSCRIPTION_KEY=${IAS_SUBSCRIPTION_KEY} \
        COUNTRY=${COUNTRY_CONSUMER} \
        CNAME=${CNAME_CONSUMER} \
        CONSUMER_HOST_NAME=${CNAME_CONSUMER} \
        docker compose down
    )
}

########################################
# Main
########################################

echo "Restart containers on consumer01.vddpi"
(
    cd $vddpi_dir
    MODE=eval-03 make gramine-consumer
    if [ "$parallel_index" -gt 0 ]; then
        stop_consumer $parallel_index $vddpi_dir
        cp $vddpi_dir/consumer/cache/* $vddpi_dir/consumer-$parallel_index/cache/
        run_consumer $parallel_index $vddpi_dir
    else
        make stop-consumer > /dev/null 2>&1
        MODE=eval-03 make run-consumer
    fi
)

echo "Run gencert (instance:$parallel_index)"
python3 $vddpi_bench_dir/client.py gencert "$cache_dir" "consumer01.vddpi" $MANAGE_PORT

echo "Run processing data (instance:$parallel_index)"
for token in $cache_dir/token-*
do
    start_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
    start_epoch=$(date +%s%3N)

    msg=$(python3 $vddpi_bench_dir/client.py process "$token" "$cache_dir" "consumer01.vddpi" $APP_PORT)

    end_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
    end_epoch=$(date +%s%3N)
    duration=$((end_epoch - start_epoch))

    echo "$msg" | head -n 1
    log=$(echo "$msg" | grep "Session completed" | sed -n 's/.*(\(.*\)).*/\1/p')
    echo "___BENCH___ Data processing (start_total:$start_ts, end_total:$end_ts, duration_total_ms:$duration, $log)" >> "$LOGFILE"
done
