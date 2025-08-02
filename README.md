# VDDPI: Verifiable Decentralized Data Processing Infrastructure

## Overview

VDDPI is a verifiable decentralized data processing infrastructure which is characterized by verifiable the data processing in advance. This verification is performed in the registry and the data provider can get the verification result when data providers receive the data usage application. This verification is independent of a single point of failure because it is performed using the smart contract and recorded in distributed ledgers. This repository provides a proof of concept (PoC), not a product release.

## Files and Directories

```
Prototype/
├── consumer/ : Files for running data processing app
├── init/ : Files for demo setup
|   ├── options/ : Files for instructions
|   ├── functions/ : Files for describing script commands
|   └── registry_setup.sh : Script to register filters and functions for demo
├── docker/ : Dockerfiles and required files for building docker images
|   ├── analyzer/ : Files for the source code analyzer
|   ├── api_registry/ : Files for the registry's API server
|   ├── ca/ : Files for the certificate authority
|   ├── db/ : Files for the provider's database
|   ├── datatype/ : Files for data schemes for provided data
|   ├── gramine_base/ : Files for building the gramine container image
|   ├── gramine_consumer/ : Files for execution the data processing app in data consumer
|   ├── gramine_registry/ : Files for the registry's app build system
|   ├── provider/ : Files for the data provision server
|   ├── psuedo_api/ : Files for the psuedo API server for data usage control
|   └── psuedo_ias/ : Files for the psuedo API server for EPID-based remote attestation
├── proverif/ : Files for formal verification
|   ├── main.log : Verification results
|   └── main.pv : Model for formal verification of the VDDPI protocol
├── provider/ : Files for the data provision server
|   ├── data/ : Files for provided data
|   └── files/ : Files required by the data provision server
├── registry/ : Files for running the data processing app registry
|   ├── application/ : Files for the registration
|   ├── chaincodes/ : Files for installing chaincodes
|   |   ├── chaincode1/ : Files for the chaincode about registration the source code
|   |   └── chaincode2/ : Files for the chaincode about functions
|   ├── fablo : script to build the Hyperledger Fabric network
|   └── fablo-config.json : Config file for building the Hyperledger Fabric network
├── Makefile : Makefile for building docker images and startup
├── load_baseimage.sh : Script for loading gramine base image
├── run_demo.sh : Script for running demo
├── set_addr.sh : Script for setting IP address
└── README.md
```



## How to run demo

1. Prepare to use Gramine-SGX and Hyperledger Fabric
   - [Set up the host environment - Gramine documentation](https://gramine.readthedocs.io/en/latest/sgx-setup.html)
   - [Prerequisites - Hyperledger Fabric Docs main documentation](https://hyperledger-fabric.readthedocs.io/en/latest/prereqs.html)
2. Clone this repository

```bash
$ git clone https://github.com/VDDPI/VDDPI.git
```

2. Set IP address (Data consumer must use an SGX-enabled machine.)

```bash
$ ./set_addr.sh [Registry IP Address] [Provider IP Address] [Consumer IP Address]
```

4. Start a fabric network (registry) and data provision server (provider)

```bash
$ make run-registry && make run-provider
```

5. Start a data processing app (consumer)

```bash
$ make run-consumer
```

6. Run demo on the consumer side

```bash
$ ./run_demo.sh
```

### Modify the data processing code

If you want to change the data processing code, in addition to changing `consumer/code/main.py`, you need to register with the registry and change the data provision policy.

## Formal Verification with ProVerif

### VSCode

This repository provides `.devcontainer`.  So you can run proverif in a development container if you are using Visual Studio Code.

Details about devcontainer: [Developing inside a Container - Visual Studio Code](https://code.visualstudio.com/docs/devcontainers/containers)



### Building docker container and running proverif

If you are not using VSCode, you can use below commands to run proverif.

```bash
$ docker build -t proverif .devcontainer
$ docker run --rm -it -v ${PWD}/proverif:/home/root/ proverif bash -c "cd ../root/ && proverif main.pv"
```

***
### References

#### [gramineproject/gramine](https://github.com/gramineproject/gramine)

> A library OS for Linux multi-process applications, with Intel SGX support

Gramine is used for running the data processing app.

#### [hyperledger/fabric](https://github.com/hyperledger/fabric)

> Hyperledger Fabric is an enterprise-grade permissioned distributed ledger framework for developing solutions and applications. Its modular and versatile design satisfies a broad range of industry use cases. It offers a unique approach to consensus that enables performance at scale while preserving privacy.

Hyperledger Fabric is used as distributed ledger technology.

#### [Hyperledger-labs/fablo](https://github.com/hyperledger-labs/fablo)

> Fablo is a simple tool to generate the Hyperledger Fabric blockchain network and run it on Docker. It supports RAFT and solo consensus protocols, multiple organizations and channels, chaincode installation and upgrade.

Fablo is used for running the data processing app registry.

#### [python/cpython](https://github.com/python/cpython)

> The Python programming language

The CPython interpreter is used for executing the data processing app.
