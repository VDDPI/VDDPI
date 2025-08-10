#! /bin/bash

# set -x

python3 ../registry/application/registry-client.py -r 1 user1 user1pw > /dev/null
python3 ../registry/application/registry-client.py 1 user1 user1pw -f options/registerID.txt > /dev/null

python3 ../registry/application/registry-client.py -r 2 user2 user2pw > /dev/null
python3 ../registry/application/registry-client.py 2 user2 user2pw -f options/registerID.txt > /dev/null

python3 ../registry/application/registry-client.py -r 3 user3 user3pw > /dev/null
python3 ../registry/application/registry-client.py 3 user3 user3pw -f options/registerID.txt > /dev/null

python3 ../registry/application/registry-client.py 1 user1 user1pw -f options/suggest.txt > /dev/null
python3 ../registry/application/registry-client.py 1 user1 user1pw -f options/vote.txt > /dev/null
python3 ../registry/application/registry-client.py 2 user2 user2pw -f options/vote.txt > /dev/null
python3 ../registry/application/registry-client.py 3 user3 user3pw -f options/vote.txt > /dev/null

echo "Registry initialized"
