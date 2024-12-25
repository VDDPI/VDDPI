#!/bin/bash

# set -x

if [ $# -ne 3 ]; then
    echo "Usage: ./setup.sh [AR IP Addr] [DP IP Addr] [DC IP Addr]"
    exit 1
fi

AR_ADDR="$1"
DP_ADDR="$2"
DC_ADDR="$3"

# AR
## gen_cert.py
sed -i "140s/.*/    apiURL = \'http:\/\/${AR_ADDR}:8004\/sgx\/dev\/attestation\/v4\/report\/\'/" docker/gramine_base/gramine-python/gen_cert.py

## registries
sed -i "s/\/\/.*:/\/\/${AR_ADDR}:/g" provider/files/registries

## template.py
sed -i "76s/.*/    TRUSTED_TIME_API_URL = \"https:\/\/${AR_ADDR}:8005\/time\"/" docker/analyzer/template.py
sed -i "114s/.*/    TRUSTED_GEOLOCATION_API_URL = \"https:\/\/${AR_ADDR}:8005\/location\"/" docker/analyzer/template.py

## analyzer.py
sed -i "19s/.*/DATATYPE_API_ENDPOINT = \"http:\/\/${AR_ADDR}:8003\"/" docker/analyzer/analyzer/analyzer.py

## Makefile
sed -i "41s/.*/PRIVATE_CA = ${AR_ADDR}:8001/" Makefile

## client.py
sed -i "10s/.*/PRIVATE_CA_ISSUE_URL = \"http:\/\/${AR_ADDR}:8001\/issue\"/" consumer/client.py

## psuedo_api/
openssl req -new -key docker/psuedo_api/key.pem -out docker/psuedo_api/server.csr -subj "/CN=${AR_ADDR}" 2> /dev/null
openssl x509 -req -days 365 -in docker/psuedo_api/server.csr -CA docker/psuedo_api/root.crt -CAkey docker/psuedo_api/root.key -CAcreateserial -out docker/psuedo_api/server.pem 2> /dev/null

## run_demo.sh
sed -i "22s/\/\/.*\//\/\/${AR_ADDR}\//g" run_demo.sh
sed -i "32s/ .*:/ ${AR_ADDR}:/g" run_demo.sh

# DP
## 02_create_data.sql
sed -i "4s/\/\/.*:/\/\/${DP_ADDR}:/" docker/db/02_create_data.sql
sed -i "7s/\/\/.*:/\/\/${DP_ADDR}:/" docker/db/02_create_data.sql
sed -i "10s/\/\/.*:/\/\/${DP_ADDR}:/" docker/db/02_create_data.sql
sed -i "13s/\/\/.*:/\/\/${DP_ADDR}:/" docker/db/02_create_data.sql
sed -i "16s/\/\/.*:/\/\/${DP_ADDR}:/" docker/db/02_create_data.sql

## Makefile
sed -i "40s/.*/SERVER_PROVIDER_HOST_NAME = ${DP_ADDR}/" Makefile

## run_demo.sh
sed -i "35s/\/\/.*:/\/\/${DP_ADDR}:/" run_demo.sh
sed -i "36s/\/\/.*:/\/\/${DP_ADDR}:/" run_demo.sh
sed -i "37s/\/\/.*:/\/\/${DP_ADDR}:/" run_demo.sh
sed -i "38s/\/\/.*:/\/\/${DP_ADDR}:/" run_demo.sh
sed -i "39s/\/\/.*:/\/\/${DP_ADDR}:/" run_demo.sh

# DC
## client.py
sed -i "21s/.*/    tls_socket.connect((\'${DC_ADDR}\', 8001))/" consumer/client.py
sed -i "42s/.*/    tls_socket.connect((\'${DC_ADDR}\', 8002))/" consumer/client.py

echo "OK"
