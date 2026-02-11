#!/bin/bash
set -euo pipefail

INDEX="$1"

DST_PATH=./consumer_$INDEX

rm -rf $DST_PATH
cp -r ./consumer $DST_PATH

eval "$(./x_calc_eval_consumer_port.sh $INDEX)"

sed -i "s|CONSUMER_NAME=gramine-consumer|CONSUMER_NAME=gramine-consumer-$INDEX|g" $DST_PATH/.env
sed -i "s|CONSUMER_MANAGE_PORT=8001|CONSUMER_MANAGE_PORT=${CONSUMER_MANAGE_PORT}|g" $DST_PATH/.env
sed -i "s|CONSUMER_APP_PORT=8002|CONSUMER_APP_PORT=${CONSUMER_APP_PORT}|g" $DST_PATH/.env

rm -f $DST_PATH/logs/*
rm -f $DST_PATH/cache/*
rm -f $DST_PATH/certs/*
