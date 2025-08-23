#!/bin/bash

cp /dev/null consumer/code/tokens

# Phase1: register the data processing app
echo "=================== Phase1: Register your data processing app ==================="
echo "Please start the registry (\$make run-registry)."
echo ""
read -p "If the registry is running, press Enter to continue..."

echo "Registring..."
curl -X 'POST' \
  'http://192.168.220.5/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'program=@consumer/code/main.py;type=text/x-python' \
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

curl 192.168.220.5:8001/root-crt > consumer/code/RootCA.pem
(
	cd consumer && echo -e "JP\n\n\n\n\nconsumer.example.com\n\n\n\n" | python3 get_cert.py 192.168.220.5:8001
)

./run_data_usage_application.sh $APP_ID

# Phase3: process data
echo "============================== Phase3: Process data =============================="
make run-consumer

echo "Waiting for 20 seconds to start consumer..."
sleep 20

cd consumer && python3 client.py
