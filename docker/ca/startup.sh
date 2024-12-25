#! /bin/bash

# set -x
openssl req -new -x509 -newkey rsa:2048 -passout pass:test -out /etc/ssl/CA/cacert.pem -keyout /etc/ssl/CA/private/cakey.pem -subj "/C=JP/CN=private-ca.example.com" -days 365
python3 main.py
