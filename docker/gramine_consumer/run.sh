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

echo "=== Starting Python SGX Command Server ==="

# Check if Python3 is available
if ! command -v /usr/bin/python3 >/dev/null 2>&1; then
    echo "Error: Python3 is not installed"
    exit 1
fi

# Create server.py if it doesn't exist
if [ ! -f server.py ]; then
    echo "Error: server.py not found in current directory"
    echo "Please ensure server.py is in the same directory as this script"
    exit 1
fi

# Start Python server
echo "Starting Python SGX server on port $SERVER_PORT..."
if [ -n "$VERBOSE_FLAG" ]; then
    echo "Verbose logging enabled"
fi

# Start the Python server
/usr/bin/python3 server.py --port "$SERVER_PORT" --verbose
