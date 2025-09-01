#!/bin/bash

mode="$1"

(cd consumer && python3 client.py gencert)

if [ "$mode" = "eval-01" ]; then
	for i in $(seq 1 10); do
		num=$(printf "%03d" "$i")
    (cd consumer && python3 client.py process cache/token-$num)
	done
else
  (cd consumer && python3 client.py process cache/tokens)
fi