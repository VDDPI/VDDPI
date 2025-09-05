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

        msg=$(python3 ../client.py process "$token" "$cache_dir")

        echo "$msg" | head -n 1
        log=$(echo "$msg" | grep "Session completed" | sed -n 's/.*(\(.*\)).*/\1/p')
        case "$log" in
            *"cached:True"*)
                logfile="$LOGFILE_CACHE"
                ;;
            *"cached:False"*)
                logfile="$LOGFILE_NOCACHE"
                ;;
            *)
                echo "Error: Unexpected log format: $log"
                exit 1
                ;;
        esac
        echo "___BENCH___ Data processing ($log)" >> "$logfile"
    done
done
