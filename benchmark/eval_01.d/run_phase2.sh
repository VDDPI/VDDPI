#!/bin/bash

########################################
# Configuration
########################################
LOGFILE="result/eval_data_usage_application.log"

########################################
# Arguments
########################################
app_id="$1"
trial_count="$2"
provider_db_config="$3"

########################################
# Functions
########################################
function insert_policy() {
    local data_id_="$1"
    local mrenclave="$2"
    local provider_db_config="$3"

    local values="('provider.example.com','person','$data_id','consumer.example.com','$mrenclave','',5,'JP',90,'2026-12-01')"
    local sql="INSERT INTO policy (data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date) VALUES $values"

    mysql --defaults-file=$provider_db_config provider -e "$sql"
}

########################################
# Main
########################################
# Clear file
> $LOGFILE

until mysqladmin --defaults-file=$provider_db_config ping --silent
do
	echo "MySQL is not ready..."
	sleep 2
done

curl registry01.vddpi:8001/root-crt > ./cache/RootCA.pem
(
	echo -e "JP\n\n\n\n\nconsumer.example.com\n\n\n\n" | python3 ../get_cert.py registry01.vddpi:8001 ./cache
)

for i in $(seq 1 $trial_count)
do
    index=$(printf "%03d" "$i")
    data_id=$(printf "https://provider01.vddpi:443/data/person/personal-%03d" "$index")
    insert_policy "$data_id" "$app_id" "$provider_db_config"

    start_ts=$(date +"%Y-%m-%d %H:%M:%S")
    start_epoch=$(date +%s%3N)
    python3 ../create_declaration.py \
        -o ./cache/token-$index \
        consumer.example.com $app_id $data_id 1 ./cache/consumer.key
    end_ts=$(date +"%Y-%m-%d %H:%M:%S")
    end_epoch=$(date +%s%3N)

    duration=$((end_epoch - start_epoch))
    echo "___BENCH___ Data usage application (Start:$start_ts, End:$end_ts, Duration_ms:$duration)" >> "$LOGFILE"
done