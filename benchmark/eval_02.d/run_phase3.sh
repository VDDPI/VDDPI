#!/bin/bash

########################################
# Configuration
########################################
PATH_LOGFILE_BASE="result/eval_data_processing_cache"

########################################
# Arguments
########################################
vddpi_dir="$1"
vddpi_bench_dir="$2"
cache_dir="$3"


########################################
# Main
########################################

echo "Restart containers on consumer01.vddpi"
(
    cd $vddpi_dir
    make stop-consumer > /dev/null 2>&1
    MODE=eval-02 make run-consumer
)

# The first loop iteration retrieves data from the provider; the second iteration uses that data as cache.
echo "Run gencert"
python3 $vddpi_bench_dir/client.py gencert "$cache_dir"

for f in 1k 2k 3k 4k 5k 6k 7k 8k 9k 10k
do
    logfile=$PATH_LOGFILE_BASE-$f.log

    # Clear file
    > "$logfile"

    for scenario in "no_cache" "cache01" "cache02" "cache03" "cache04" "cache05" "cache06" "cache07" "cache08" "cache09" "cache10"
    do

        echo "Run processing data (scenario:$scenario)"
        start_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
        start_epoch=$(date +%s%3N)

        token=$cache_dir/token-$f
        msg=$(python3 $vddpi_bench_dir/client.py process "$token" "$cache_dir")

        end_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
        end_epoch=$(date +%s%3N)
        duration=$((end_epoch - start_epoch))

        echo "$msg" | head -n 1
        log=$(echo "$msg" | grep "Session completed" | sed -n 's/.*(\(.*\)).*/\1/p')

        if [[ $scenario == cache* ]]; then
            echo "___BENCH___ Data processing (start_total:$start_ts, end_total:$end_ts, duration_total_ms:$duration, $log)" >> "$logfile"
        fi
    done
done