#!/bin/bash

########################################
# Configuration
########################################
LOGFILE_CACHE="result/eval_data_processing_cache.log"
LOGFILE_NOCACHE="result/eval_data_processing_nocache.log"

########################################
# Arguments
########################################
cache_dir="$1"

########################################
# Initialization
########################################
> "$LOGFILE_CACHE"
> "$LOGFILE_NOCACHE"

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

        start_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
        start_epoch=$(date +%s%3N)

        msg=$(python3 ../client.py process "$token" "$cache_dir")

        end_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
        end_epoch=$(date +%s%3N)
        duration=$((end_epoch - start_epoch))

        echo "$msg" | head -n 1
        log=$(echo "$msg" | grep "Session completed" | sed -n 's/.*(\(.*\)).*/\1/p')
        case "$scenario" in
            "no_cache")
                logfile="$LOGFILE_NOCACHE"
                ;;
            "cache")
                logfile="$LOGFILE_CACHE"
                ;;
            *)
                echo "Error: Unexpected log format: $log"
                exit 1
                ;;
        esac
        echo "___BENCH___ Data processing (start:$start_ts, end:$end_ts, duration_ms:$duration, $log)" >> "$logfile"
    done
done
