#!/bin/bash

########################################
# Configuration
########################################
INTERVAL="${INTERVAL:-5}"

########################################
# Main
########################################
# Output CSV header
echo "Timestamp,Container,MemUsage,CPU%,NetI/O,BlockI/O"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    # Get docker stats output once and add timestamp
    docker stats --no-stream --format "table {{.Container}},{{.MemUsage}},{{.CPUPerc}},{{.NetIO}},{{.BlockIO}}" registry-v1-analyzer-1 registry-v1-gramine-1 | \
    tail -n +2 | \
    while read line; do
        echo "$TIMESTAMP,$line"
    done
    
    sleep $INTERVAL
done
