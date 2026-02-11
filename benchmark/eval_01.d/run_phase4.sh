#!/bin/bash

########################################
# Arguments
########################################
vddpi_dir="$1"
trial_count="$2"

########################################
# Main
########################################
(
    cd $vddpi_dir
    make stop-consumer-benchmark-nosgx
    DATA_NUM=$trial_count make run-consumer-benchmark-nosgx
)