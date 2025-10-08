#!/bin/bash

python3 lib/gen-graph-data-privacyguard.py ./result/privacyguard.log ./result/graph-data-privacyguard.json
python3 lib/gen-graph-data-vddpi.py ./result ./result/graph-data-vddpi.json
python3 lib/gen-graph.py \
    ./result/graph-data-vddpi.json \
    ./result/graph-data-privacyguard.json \
    --order enclave_initializing policy_checking processing \
    --order processing policy_checking enclave_initializing \
    --label-a "VDDPI" --label-b "PrivacyGuard" \
    --output ./result/graph-eval-02.svg
