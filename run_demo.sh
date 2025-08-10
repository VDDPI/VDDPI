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

echo -e "consumer.example.com\n803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512\nhttps://192.168.220.7:443/data/person/personal-001\n1\n5\nJP\n30\n2024-12-31\n" | python3 create_declaration.py
echo -e "consumer.example.com\n803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512\nhttps://192.168.220.7:443/data/person/personal-002\n2\n5\nJP\n30\n2024-12-31\n" | python3 create_declaration.py
echo -e "consumer.example.com\n803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512\nhttps://192.168.220.7:443/data/person/personal-003\n3\n5\nJP\n30\n2024-12-31\n" | python3 create_declaration.py
echo -e "consumer.example.com\n803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512\nhttps://192.168.220.7:443/data/person/personal-004\n4\n5\nJP\n30\n2024-12-31\n" | python3 create_declaration.py
echo -e "consumer.example.com\n803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512\nhttps://192.168.220.7:443/data/person/personal-005\n5\n5\nJP\n30\n2024-12-31\n" | python3 create_declaration.py

# Phase3: process data
echo "============================== Phase3: Process data =============================="
cd .. && make run-consumer

echo "Waiting for 20 seconds to start consumer..."
sleep 20

cd consumer && python3 client.py
