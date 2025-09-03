#!/bin/bash

########################################
# Configuration
########################################
LOGFILE="result/eval_data_processing.log"

########################################
# Arguments
########################################
cache_dir="$1"

########################################
# Initialization
########################################
> "$LOGFILE"

########################################
# Main
########################################
python3 ../client.py gencert "$cache_dir"

# The first loop iteration retrieves data from the provider; the second iteration uses that data as cache.
for scenario in "no_cache" "cache"
do
    echo "Run processing data (scenario:$scenario)"
    for token in $cache_dir/token-*
    do
        start_ts=$(date +"%Y-%m-%d %H:%M:%S")
        start_epoch=$(date +%s%3N)

        msg=$(python3 ../client.py process "$token" "$cache_dir")

        end_ts=$(date +"%Y-%m-%d %H:%M:%S")
        end_epoch=$(date +%s%3N)
        duration=$((end_epoch - start_epoch))

        echo "$msg" | head -n 1
        log=$(echo "$msg" | grep "Session completed" | sed -n 's/.*(\(.*\)).*/\1/p')
        echo "___BENCH___ App registration (Start:$start_ts, End:$end_ts, Duration_ms:$duration, scenario:$scenario, $log)" >> "$LOGFILE"
    done
done
