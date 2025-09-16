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

if [ "$mode" = "eval-01" ]; then
    rm -f ./data/person/*
    python3 ./make_test_data.py "$num_files" data/person 0;
elif [ "$mode" = "eval-02" ]; then
    rm -f ./data/svm/*
    cp /svm_data/* ./data/svm
else
    echo "Unknown mode: $mode"
    exit 1
fi