#!/bin/bash

mode="$1"

(cd consumer && python3 client.py consumer01.vddpi 8080 http://registry01.vddpi:8001/issue gencert)

if [ "$mode" = "eval-01" ]; then
	for i in $(seq 1 10); do
		num=$(printf "%03d" "$i")
    (cd consumer && python3 client.py consumer01.vddpi 8080 http://registry01.vddpi:8001/issue process cache/token-$num)
	done
else
  (cd consumer && python3 client.py consumer01.vddpi 8080 http://registry01.vddpi:8001/issue process cache/tokens)
fi