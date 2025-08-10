#!/bin/bash

declare -A registriesCC1=(
    ["dev-peer0.registry1.example.com-chaincode1"]="registry_v1-network"
    ["dev-peer0.registry2.example.com-chaincode1"]="registry_v2-network"
    ["dev-peer0.registry3.example.com-chaincode1"]="registry_v3-network"
)

declare -A registriesCC2=(
    ["dev-peer0.registry1.example.com-chaincode2"]="registry_v1-network"
    ["dev-peer0.registry2.example.com-chaincode2"]="registry_v2-network"
    ["dev-peer0.registry3.example.com-chaincode2"]="registry_v3-network"
)

declare -A registry_API=(
    ["registry-network_v1-api_1"]="registry_v1-network"
    ["registry-network_v2-api_1"]="registry_v2-network"
    ["registry-network_v3-api_1"]="registry_v3-network"
)

declare -A registry_peers=(
    ["peer0.registry1.example.com"]="registry_v1-network"
    ["peer0.registry2.example.com"]="registry_v2-network"
    ["peer0.registry3.example.com"]="registry_v3-network"
)

declare -A registry_ca=(
    ["ca.registry1.example.com"]="registry_v1-network"
    ["ca.registry2.example.com"]="registry_v2-network"
    ["ca.registry3.example.com"]="registry_v3-network"
)

declare -A registry_cli=(
    ["cli.registry1.example.com"]="registry_v1-network"
    ["cli.registry2.example.com"]="registry_v2-network"
    ["cli.registry3.example.com"]="registry_v3-network"
)

declare -A registry_fablo_rest=(
    ["fablo-rest.registry1.example.com"]="registry_v1-network"
    ["fablo-rest.registry2.example.com"]="registry_v2-network"
    ["fablo-rest.registry3.example.com"]="registry_v3-network"
)

for CC1 in ${!registriesCC1[@]}
do
    container=`docker ps -f "name=$CC1" -q`
    docker network connect ${registriesCC1[$CC1]} $container || docker network connect ${registriesCC1[$CC1]} $container || exit 1
done

for CC2 in ${!registriesCC2[@]}
do
    container=`docker ps -f "name=$CC2" -q`
    docker network connect ${registriesCC2[$CC2]} $container || docker network connect ${registriesCC2[$CC2]} $container || exit 1
done

for peer in ${!registry_peers[@]}
do
    container=`docker ps -f "name=$peer" -f "ancestor=hyperledger/fabric-peer:2.4.0" -q`
    docker network connect ${registry_peers[$peer]} $container || docker network connect ${registry_peers[$peer]} $container || exit 1
done

for ca in ${!registry_ca[@]}
do
    container=`docker ps -f "name=$ca" -f "ancestor=hyperledger/fabric-ca:1.5.0" -q`
    docker network connect ${registry_ca[$ca]} $container || docker network connect ${registry_ca[$ca]} $container || exit 1
done

for cli in ${!registry_cli[@]}
do
    container=`docker ps -f "name=$cli" -f "ancestor=hyperledger/fabric-tools:2.4.0" -q`
    docker network connect ${registry_cli[$cli]} $container || docker network connect ${registry_cli[$cli]} $container || exit 1
done

for rest in ${!registry_fablo_rest[@]}
do
    container=`docker ps -f "name=$rest" -q`
    docker network connect ${registry_fablo_rest[$rest]} $container || docker network connect ${registriesCC1[$CC1]} $container || exit 1
done
