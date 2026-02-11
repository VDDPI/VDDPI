#!/bin/sh

python3 lib/gen-graph-data.py \
    result/run.log \
    result/consumer_host_stats.csv \
    result/graph_data.json

python3 lib/gen-graph.py \
    result/graph_data.json \
    result/graph_cpu_mem_multi_dc.svg
