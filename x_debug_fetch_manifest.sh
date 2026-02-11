#!/bin/bash

docker exec gramine-consumer cat python.manifest.sgx > /tmp/python.manifest.consumer.sgx
ssh registry01.vddpi "docker exec registry-v1-gramine-1 cat /root/python.manifest.sgx" > /tmp/python.manifest.registry.sgx

docker exec gramine-consumer cat python.manifest > /tmp/python.manifest.consumer
ssh registry01.vddpi "docker exec registry-v1-gramine-1 cat /root/python.manifest" > /tmp/python.manifest.registry
