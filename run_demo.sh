#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 <mode>"
    echo ""
    echo "Mode"
    echo "  demo"
    echo "  eval-01"
    exit 1
fi

mode="$1"

cp /dev/null consumer/cache/tokens

# Phase1: register the data processing app
echo "=================== Phase1: Register your data processing app ==================="
echo "Please start the registry (\$make run-registry)."
echo ""
read -p "If the registry is running, press Enter to continue..."

file="docker/gramine_consumer/code/main.py"
if [ "$mode" = "eval-01" ]; then
	file="docker/gramine_consumer/code_eval_01/main.py"
fi

echo "Registring..."
curl -X 'POST' \
  'http://registry01.vddpi/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F "program=@${file};type=text/x-python" \
  -F 'SPID=1234567890abcdef1234567890abcdef' \
  -F 'isLinkable=0' | tee /tmp/response.json | jq .

APP_ID=$(cat /tmp/response.json | jq -r '.DataProcessingSpec.App_ID')

# Phase2: Apply for data usage
echo "========================== Phase2: Apply for data usage =========================="
echo "Before starting the provider, make sure to set the App ID in \`docker/db/02_create_data.sql\`."
echo ""
echo "  App ID: $APP_ID"
echo ""
echo "After that, start the provider (\$make run-provider)."
echo ""
read -p "Press Enter to continue once everything is ready..."

curl registry01.vddpi:8001/root-crt > consumer/cache/RootCA.pem
(
	cd consumer && echo -e "JP\n\n\n\n\nconsumer.example.com\n\n\n\n" | python3 get_cert.py registry01.vddpi:8001
)

./run.d/run_data_usage_application.sh $APP_ID $mode

# Phase3: process data
echo "============================== Phase3: Process data =============================="
make MODE=$mode run-consumer

echo "Waiting for 20 seconds to start consumer..."
sleep 20

./run.d/run_phase3.sh $mode
