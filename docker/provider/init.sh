#!/bin/bash

mode="$1"

if [ "$mode" = "eval-01" ]; then
    num_files="$2"
    rm -f ./data/person/*
    python3 ./make_test_data.py "$num_files" data/person 0;
elif [ "$mode" = "eval-02" ]; then
    rm -f ./data/svm/*
    cp /svm_data/* ./data/svm
else
    echo "Unknown mode: $mode"
    exit 1
fi