#!/bin/bash
set -euo pipefail

INDEX="$1"

if [ -z "$INDEX" ]; then
    echo "Usage: $0 <index>"
    exit 1
fi

BASE_PORT=18000
manage_port=$(( BASE_PORT + (INDEX * 2) - 1 ))
app_port=$(( manage_port + 1 ))

echo "CONSUMER_MANAGE_PORT=$manage_port"
echo "CONSUMER_APP_PORT=$app_port"