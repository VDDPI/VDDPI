#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: ./run_in_container.sh [SPID] [IS_LINKABLE]"
    exit 1
fi

# \r\n --> \n
tr -d "\r" < /upload/main.py > /root/code/main.py

# build CPython interpreter
cd /cpython && ./build_cpython.sh /root/code/main.py /root/gen_cert.py > /dev/null 2>&1 && cp python /usr/bin/mypython

# build gramine
tmp_path=/tmp/mrenclave
gramine-sgx-gen-private-key -f > /dev/null
cd /root && make clean > /dev/null && MRENCLAVE=`make SGX=1 RA_TYPE=epid RA_CLIENT_SPID=$1 LINKABLE=$2 2>&1 | grep -A1 "Measurement:" | tail -n1 | awk '{print $1}'`

echo ${MRENCLAVE}
