#!/bin/bash

########################################
# Variable validation
########################################
if [ -z "$VDDPI_DIR" ]; then
    echo "Error: VDDPI_DIR is not set" >&2
    exit 1
fi

########################################
# Configuration
########################################
file="$VDDPI_DIR/docker/gramine_consumer/code_eval_01/main.py"

########################################
# Arguments
########################################
trial_count="$1"
app_id_file="$2"
logfile="$3"

########################################
# Main
########################################
for i in $(seq 1 "$trial_count"); do
    echo -ne "\rRun App Registration: $i/$count"

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

    # Extract App_ID from response
    app_id=$(jq -r '.DataProcessingSpec.App_ID' /tmp/response.json)

    # Since the APP ID does not change, only one record is kept by overwriting
    echo "$app_id" > "$app_id_file"

    echo "___BENCH___ App registration (Start:$start_ts, End:$end_ts, Duration_ms:$duration)" >> "$logfile"
done
