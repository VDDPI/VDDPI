#!/bin/bash

app_id="$1"
mode="$2"

if [ "$mode" = "eval-01" ]; then
	(
		cd consumer
		for i in $(seq 1 10); do # kakei
			num=$(printf "%03d" "$i")
			echo "create_declaration ($num)"
			python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
				-ai $app_id \
				-an 1 -di https://provider01.vddpi:443/data/person/personal-$num \
				-o cache/token-$num
		done
	)
else
	(
		cd consumer
		for i in $(seq 1 5); do
			num=$(printf "%03d" "$i")
			echo "create_declaration ($num)"
			python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
				-ai $app_id \
				-an $i -di https://provider01.vddpi:443/data/person/personal-$num \
				-a
		done
	)
fi
