#!/bin/bash

cp /dev/null consumer/code/tokens

# Phase1: register the data processing app
echo "=================== Phase3: Register your data processing app ==================="
echo "Please start the registry and provider (\$make run-registry; make run-provider)."
echo "Press Enter when the startup is completed."
while true;
do
    echo -n ">> "
    read -r input

    if [[ -z "$input" ]];
    then
        break
    fi
done

echo "Registring..."
curl -X 'POST' \
  'http://192.168.220.5/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'program=@consumer/code/main.py;type=text/x-python' \
  -F 'SPID=1234567890abcdef1234567890abcdef' \
  -F 'isLinkable=0' | jq .

# Phase2: Apply for data usage
echo "========================== Phase2: Apply for data usage =========================="

curl 192.168.220.5:8001/root-crt > consumer/code/RootCA.pem
cd consumer && echo -e "JP\n\n\n\n\nconsumer.example.com\n\n\n\n" | python3 get_cert.py 192.168.220.5:8001

python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
	-ai 9049742836e22731ced39b84c0e7d473d007bc8e9815144 \
	-an 1 -di https://192.168.220.7:443/data/person/personal-001
python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
	-ai 9049742836e22731ced39b84c0e7d473d007bc8e9815144 \
	-an 2 -di https://192.168.220.7:443/data/person/personal-002
python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
	-ai 9049742836e22731ced39b84c0e7d473d007bc8e9815144 \
	-an 3 -di https://192.168.220.7:443/data/person/personal-003
python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
	-ai 9049742836e22731ced39b84c0e7d473d007bc8e9815144 \
	-an 4 -di https://192.168.220.7:443/data/person/personal-004
python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
	-ai 9049742836e22731ced39b84c0e7d473d007bc8e9815144 \
	-an 5 -di https://192.168.220.7:443/data/person/personal-005

# Phase3: process data
echo "============================== Phase3: Process data =============================="
cd .. && make run-consumer

echo "Waiting for 20 seconds to start consumer..."
sleep 20

cd consumer && python3 client.py
