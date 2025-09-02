#!/bin/bash

logfile="run_eval_01.d/result/eval_obtaining_app_id.log"

# Clear file with an empty file.
> "$logfile"

ssh -T registry01.vddpi "docker logs registry-v1-gramine-1" 2>&1 | grep "___BENCH___" > "$logfile"
