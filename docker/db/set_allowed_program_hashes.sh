#!/bin/bash

mode="$1"

read -p "Please enter the MRENCLAVE of the program to allow: " mrenclave

source="02_create_data.sh.template"
if [ "$mode" = "eval-01" ]; then
	source="02_create_data.sh.template_eval_01"
fi

sed "s/<MRENCLAVE>/$mrenclave/g" "$source" > 02_create_data.sh
chmod +x 02_create_data.sh

