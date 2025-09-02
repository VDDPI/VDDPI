#!/bin/bash

app_id_list="$1"

logfile="run_eval_01.d/result/eval_data_usage_application.log"

# Clear file
> $logfile

curl registry01.vddpi:8001/root-crt > consumer/cache/RootCA.pem
(
	cd consumer && echo -e "JP\n\n\n\n\nconsumer.example.com\n\n\n\n" | python3 get_cert.py registry01.vddpi:8001
)

until mysqladmin ping -h provider01.vddpi -u root -proot --silent
do
	echo "MySQL is not ready..."
	sleep 2
done

data_id_num=0
for app_id in $(cat $app_id_list)
do
    data_id_num=$((data_id_num + 1))
    num=$(printf "%03d" "$data_id_num")
    ./run_eval_01.d/make_policy.sh "$app_id" "$num"
    start_ts=$(date +"%Y-%m-%d %H:%M:%S")
    start_epoch=$(date +%s%3N)
    (
        cd consumer
        python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
            -ai $app_id \
            -an 1 -di https://provider01.vddpi:443/data/person/personal-$num \
            -o cache/token-$num
    )
    end_ts=$(date +"%Y-%m-%d %H:%M:%S")
    end_epoch=$(date +%s%3N)

    duration=$((end_epoch - start_epoch))
    echo "___BENCH___ Data usage application (Start:$start_ts, End:$end_ts, Duration_ms:$duration)" >> "$logfile"
done