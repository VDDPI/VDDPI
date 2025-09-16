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
cache_dir="$4"

########################################
# Functions
########################################
function insert_policy() {
    local data_id_="$1"
    local mrenclave="$2"
    local provider_db_config="$3"

    local values="('provider.example.com','svm','$data_id','consumer.example.com','$mrenclave','svm.data',5,'JP',90,'2026-12-01')"
    local sql="REPLACE INTO policy (data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date) VALUES $values"

    mysql --defaults-file=$provider_db_config provider -e "$sql"
}

svm.########################################
# Main
########################################
# Clear file
> $LOGFILE

echo "Checking My SQL connection..."
until mysqladmin --defaults-file=$provider_db_config ping --silent
do
	echo "MySQL is not ready..."
	sleep 2
done

echo "Get root CA certificate"
curl registry01.vddpi:8001/root-crt > $cache_dir/RootCA.pem

echo "Get consumer certificate"
echo -e "JP\n\n\n\n\nconsumer.example.com\n\n\n\n" | python3 ../get_cert.py registry01.vddpi:8001 $cache_dir


data_id="https://provider01.vddpi:443/data/svm/1k"

echo "Preparing data provision policy -- provider preparation (app_id:$app_id, data_id:$data_id)"
insert_policy "$data_id" "$app_id" "$provider_db_config"

echo "Applying for data usage (app_id:$app_id, data_id:$data_id)"
start_ts=$(date +"%Y-%m-%d %H:%M:%S")
start_epoch=$(date +%s%3N)
python3 ../create_declaration.py \
    -o $cache_dir/token-$index \
    consumer.example.com "$app_id" "$data_id" 1 $cache_dir/consumer.key
end_ts=$(date +"%Y-%m-%d %H:%M:%S")
end_epoch=$(date +%s%3N)

duration=$((end_epoch - start_epoch))
echo "___BENCH___ Data usage application (Start:$start_ts, End:$end_ts, Duration_ms:$duration)" >> "$LOGFILE"