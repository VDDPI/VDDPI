#!/bin/bash

python3 lib/gen-graph-data-privacyguard.py ./result/privacyguard.log ./result/graph-data-privacyguard.json
python3 lib/gen-graph-data-vddpi.py ./result ./result/graph-data-vddpi.json
