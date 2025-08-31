#!/bin/bash

APP_ID="$1"

(
	cd consumer
	python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
		-ai $APP_ID \
		-an 1 -di https://provider01.vddpi:443/data/person/personal-001
	python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
		-ai $APP_ID \
		-an 2 -di https://provider01.vddpi:443/data/person/personal-002
	python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
		-ai $APP_ID \
		-an 3 -di https://provider01.vddpi:443/data/person/personal-003
	python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
		-ai $APP_ID \
		-an 4 -di https://provider01.vddpi:443/data/person/personal-004
	python3 create_declaration.py -subj consumer.example.com -ct 5 -loc JP -dr 30 -exd 2025-12-31 \
		-ai $APP_ID \
		-an 5 -di https://provider01.vddpi:443/data/person/personal-005
)
