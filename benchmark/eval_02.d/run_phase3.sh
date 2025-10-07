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
vddpi_eval_dir="$3"
trial_count="$4"
cache_dir="$5"

########################################
# Variables
########################################
applog_dir=$vddpi_dir/consumer/logs
applog=$applog_dir/app.log

########################################
# Main
########################################
echo "Restart containers on consumer01.vddpi"
(
    cd $vddpi_dir
    make stop-consumer > /dev/null 2>&1
)

rm -f $applog_dir/*

for f in 1k 2k 3k 4k 5k 6k 7k 8k 9k 10k
do
    logfile=$PATH_LOGFILE_BASE-$f.log

    # Clear file
    > "$logfile"
    > "$applog"

    rm -f $vddpi_dir/consumer/certs/*

    for i in $(seq 0 "$trial_count")
    do
        echo "Run processing data (file:$f, loop:$i)"
        start_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
        start_epoch=$(date +%s%3N)

        (
            cd $vddpi_dir
            MODE=eval-02 make run-consumer
        )

        if (( i == 0 )); then
            echo "Run gencert"
            for j in {1..10}; do
                sleep 1
                python3 $vddpi_bench_dir/client.py gencert "$cache_dir" && break
            done
        fi

        token=$cache_dir/token-$f
        for j in {1..10}; do
            sleep 1
            msg=$(python3 $vddpi_bench_dir/client.py process "$token" "$cache_dir") && break
        done

        end_ts=$(date +"%Y-%m-%d %H:%M:%S.%3N")
        end_epoch=$(date +%s%3N)
        duration=$((end_epoch - start_epoch))

        echo "$msg" | head -n 1
        log=$(echo "$msg" | grep "Session completed" | sed -n 's/.*(\(.*\)).*/\1/p')

        if (( $i == 0 )); then
            # Delete log file of the first run
            > "$applog"
        else
            echo "___BENCH___ Data processing (start_total:$start_ts, end_total:$end_ts, duration_total_ms:$duration, $log)" >> "$logfile"
        fi

        (
            cd $vddpi_dir
            make stop-consumer > /dev/null 2>&1
        )
    done

    mv $applog $applog_dir/app-$f.log
done

cp $applog_dir/app-*.log $vddpi_eval_dir/result/
