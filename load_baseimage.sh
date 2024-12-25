#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: ./load_baseimage.sh [saved image file path]"
    exit 1
fi

cat $1 | gzip -d | docker load
