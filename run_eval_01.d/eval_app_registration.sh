#!/bin/bash

# Usage: ./run_register.sh <file> <count>
file="$1"
count="$2"
app_list="./cache/app_id_list.txt"
logfile="run_eval_01.d/result/eval_app_registration.log"

if [ -z "$file" ] || [ -z "$count" ]; then
    echo "Usage: $0 <file> <count>"
    exit 1
fi

# Clear file with an empty file.
> "$logfile"
> "$app_list"

for i in $(seq 1 "$count"); do
    echo -ne "\rRun $i/$count"

    start_ts=$(date +"%Y-%m-%d %H:%M:%S")
    start_epoch=$(date +%s%3N)

    curl -s -X 'POST' \
        'http://registry01.vddpi/register' \
        -H 'accept: application/json' \
        -H 'Content-Type: multipart/form-data' \
        -F "program=@${file};type=text/x-python" \
        -F 'SPID=1234567890abcdef1234567890abcdef' \
        -F 'isLinkable=0' \
        > /tmp/response.json

    end_ts=$(date +"%Y-%m-%d %H:%M:%S")
    end_epoch=$(date +%s%3N)
    duration=$((end_epoch - start_epoch))

    # Extract App_ID from response and append to list file
    APP_ID=$(jq -r '.DataProcessingSpec.App_ID' /tmp/response.json)
    echo "$APP_ID" >> "$app_list"

    echo "___BENCH___ App registration (Start:$start_ts, End:$end_ts, Duration_ms:$duration)" >> "$logfile"
done

echo -e "\nAll App_IDs saved to $app_list"
