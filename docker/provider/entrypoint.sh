#!/bin/bash

########################################
# Variable validation
########################################
if [ -z "$PRIVATE_CA" ]; then
    echo "Error: PRIVATE_CA environment variable is not set"
    exit 1
fi

########################################
# Configuration
########################################
RETRY_DELAY=5
PRIVATE_CA="registry01.vddpi:8001"

echo "Downloading RootCA certificate from $PRIVATE_CA/root-crt"

# Download a root CA certificate
while true
do
    if curl -f "$PRIVATE_CA/root-crt" 2>/dev/null > files/RootCA.pem; then
        # Check if the file is not empty
        file_size=$(wc -c < files/RootCA.pem)
        if [ "$file_size" -gt 0 ]; then
            echo "RootCA.pem downloaded successfully (size:$file_size)."
            break
        else
            echo "Waiting for RootCA server to be available at $PRIVATE_CA ..."
        fi
    else
        echo "Waiting for RootCA server to be available at $PRIVATE_CA ..."
    fi
    sleep $RETRY_DELAY
done

echo "Starting main.py"
python3 main.py
