#!/bin/bash

# Script to build cpython_main with sha256 hash value added.

if [ $# -ne 2 ]; then
    echo "You must specify the path to the Python program you verify the Python program."
    echo "Usage: ./create_mypython.sh [data processing program path] [certification generation program]"
    exit 1
fi

cpython_main="./Programs/python.c"
target_file="$1"
makefile_path="./Makefile"

# change the hash value of the data processing program
target_file_hash=(`sha256sum ${target_file}`)
echo "sha256(${target_file_hash[1]}): ${target_file_hash[0]}"
sed -iE "s/#define DP_HASH_VALUE.*/#define DP_HASH_VALUE \"${target_file_hash[0]}\"/g" ${cpython_main}
echo -e "-----------------------------------------------------------------------------------------------------------------------\nThis CPython interpreter executes data processing program \"${target_file}\".\n-----------------------------------------------------------------------------------------------------------------------"

# change the hash value of the certification generation program
target_file="$2"
target_file_hash=(`sha256sum ${target_file}`)
echo "sha256(${target_file_hash[1]}): ${target_file_hash[0]}"
sed -iE "s/#define GCP_HASH_VALUE.*/#define GCP_HASH_VALUE \"${target_file_hash[0]}\"/g" ${cpython_main}

make -f ${makefile_path} > /dev/null && echo -e "-----------------------------------------------------------------------------------------------------------------------\nThe build was successful. The program executed in this CPython interpreter generate a certificate with ${target_file}.\n-----------------------------------------------------------------------------------------------------------------------"
