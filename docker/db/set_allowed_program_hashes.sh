#!/bin/bash

read -p "Please enter the MRENCLAVE of the program to allow: " mrenclave

sed "s/<MRENCLAVE>/$mrenclave/g" 02_create_data.sql.template > 02_create_data.sql

