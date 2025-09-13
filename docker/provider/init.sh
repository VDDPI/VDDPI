#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <mode>"
    echo ""
    echo "mode:"
    echo "  - demo" # To be implemented
    echo "  - eval-01 <num_files>"
    exit 1
fi

mode="$1"
num_files="$2"

rm -f provider/data/person/*
if [ "$mode" = "eval-01" ]; then
    python3 ./make_test_data.py "$num_files" data/person 0;
fi