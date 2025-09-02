#!/bin/bash

INTERVAL="${1:-5}"

# ヘッダーを作成
echo "Timestamp,Container,MemUsage,CPU%,NetI/O,BlockI/O"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    # docker statsの出力を1回だけ取得し、タイムスタンプを付加
    docker stats --no-stream --format "table {{.Container}},{{.MemUsage}},{{.CPUPerc}},{{.NetIO}},{{.BlockIO}}" registry-v1-analyzer-1 registry-v1-gramine-1 | \
    tail -n +2 | \
    while read line; do
        echo "$TIMESTAMP,$line"
    done
    
    sleep $INTERVAL
done
