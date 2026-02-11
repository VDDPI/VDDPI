#!/bin/bash

# set -x

if [ $# -ne 0 ]; then
    echo "Usage: ./run.sh"
    exit 1
fi

# install root CA cert
curl ${PRIVATE_CA}/root-crt > code/RootCA.pem

# build python interpreter
#cd /cpython && ./build_cpython.sh /root/code/main.py /root/gen_cert.py 2> /dev/null && cp python /usr/bin/mypython

./../restart_aesm.sh 

if [ ! -f certs/client.pem ]; then
    echo "========= Start generating certificate =========="
    gramine-sgx ./python -gencert
    echo "========= Finish generating certificate =========="
else
    echo "Certificate already exists, skip generating certificate"
fi

# execute data processing 
echo "========= Start data processing app =========="
while true; do
    gramine-sgx ./python code/main.py
    sleep 1
done
echo "========= Finish data processing app =========="