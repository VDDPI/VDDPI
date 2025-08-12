#!/bin/bash

# set -x

if [ $# -ne 0 ]; then
    echo "Usage: ./run.sh"
    exit 1
fi

# install root CA cert
curl ${PRIVATE_CA}/root-crt > code/RootCA.pem

# build python interpreter
cd /cpython && ./build_cpython.sh /root/code/main.py /root/gen_cert.py 2> /dev/null && cp python /usr/bin/mypython

./../restart_aesm.sh 

echo "========= Start build data processing app =========="
# build gramine
gramine-sgx-gen-private-key -f > /dev/null
cd /root && make clean > /dev/null && make SGX=1 RA_TYPE=dcap RA_CLIENT_SPID=${SPID} LINKABLE=${IS_LINKABLE}
echo "========= Finish build data processing app =========="

echo "========= Start generating certificate =========="
gramine-sgx ./python -gencert
echo "========= Finish generating certificate =========="

# execute data processing 
echo "========= Start data processing app =========="
gramine-sgx ./python code/main.py

echo "========= Finish data processing app =========="
# /bin/bash
