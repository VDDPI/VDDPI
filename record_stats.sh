#!/bin/bash

echo "timestamp,cpu_usage_percent,mem_used_mb" | tee consumer_host_stats.csv

while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S'),$(top -bn1 | grep "Cpu(s)" | awk '{print $2+$4}'),$(free -m | awk '/Mem:/ {print $3}')"
    sleep 1
done | tee -a consumer_host_stats.csv
