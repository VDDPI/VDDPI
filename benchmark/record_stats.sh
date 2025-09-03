#!/bin/bash

########################################
# Configuration
########################################
INTERVAL="${INTERVAL:-5}"

########################################
# Arguments
########################################
CONTAINERS=("$@")

########################################
# Varidation
########################################
if [ ${#CONTAINERS[@]} -eq 0 ]; then
    echo "Usage: $0 <container1> [container2 ...]"
    exit 1
fi

########################################
# Main
########################################
# Output CSV header
echo "Timestamp,Container,MemUsage,CPU%,NetI/O,BlockI/O"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    # Get docker stats output once and add timestamp
    docker stats --no-stream --format "table {{.Container}},{{.MemUsage}},{{.CPUPerc}},{{.NetIO}},{{.BlockIO}}" ${CONTAINERS[@]} | \
    tail -n +2 | \
    while read line; do
        echo "$TIMESTAMP,$line"
    done
    
    sleep $INTERVAL
done
