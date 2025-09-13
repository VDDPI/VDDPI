#!/bin/bash
set -e

DATA_NUM="${DATA_NUM:-1000}"

rm -rf ./cache/eval_01

mkdir -p ./cache/eval_01/data
mkdir -p ./cache/eval_01/data_enc

# Generate test data
echo "Generating $DATA_NUM test data..."
python3 ./make_test_data.py "$DATA_NUM" ./cache/eval_01/data

# Encrypt test data
echo "Encrypting test data..."
python3 ./encdec.py encrypt \
    --in-dir ./cache/eval_01/data \
    --out-dir ./cache/eval_01/data_enc \
    --gen-key-file ./cache/eval_01/secret.key \
    --gen-key-size 16

# Measurement of Benchmark
echo "Running benchmark..."
python3 ./eval_01.py \
    ./lib \
    code_eval_01_main \
    ./cache/eval_01/data_enc \
    ./cache/eval_01/secret.key \
    ./cache/eval_01/log.txt \
    --silent