#!/bin/bash

mrenclave="$1"
data_id_num="$2"

function insert_policy() {
    data_provider="${1}"
    data_type="${2}"
    data_id="${3}"
    data_consumer="${4}"
    data_processing="${5}"
    data_disclosing="${6}"
    data_counter="${7}"
    data_location="${8}"
    data_duration="${9}"
    data_expiration_date="${10}"

    mysql -h provider01.vddpi -u root -proot provider > /dev/null 2>&1 <<-EOSQL
        INSERT INTO policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
        VALUES ("$data_provider", "$data_type", "$data_id", "$data_consumer", "$data_processing", "$data_disclosing", "$data_counter", "$data_location", "$data_duration", "$data_expiration_date");
EOSQL
}

data_id=$(printf "https://provider01.vddpi:443/data/person/personal-%03d" "$data_id_num")
values="('provider.example.com','person','$data_id','consumer.example.com','$mrenclave','',5,'JP',90,'2026-12-01')"

sql="INSERT INTO policy (data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date) VALUES $values"
mysql -h provider01.vddpi -u root -proot provider -e "$sql"