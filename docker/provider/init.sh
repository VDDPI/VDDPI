#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <mode>"
    echo ""
    echo "mode:"
    echo "  - demo" # To be implemented
    echo "  - eval-01"
    exit 1
fi

mode="$1"

rm -f provider/data/person/*
if [ "$mode" = "eval-01" ]; then
    python3 ./make_test_data.py 100 0;
fi