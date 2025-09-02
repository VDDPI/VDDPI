#!/bin/bash

logfile="run_eval_01.d/result/eval_code_analysis.log"

# Clear file with an empty file.
> "$logfile"

ssh -T registry01.vddpi "docker logs registry-v1-analyzer-1" | grep "___BENCH___" > "$logfile"
