DOCKER_CMD = docker
DOCKER_COMPOSE_CMD = docker compose

SPID = 1234567890abcdef1234567890abcdef
IS_LINKABLE = 0
IAS_SUBSCRIPTION_KEY = 1234567890abcdef1234567890abcdef
COUNTRY_CONSUMER = JP
CNAME_CONSUMER = consumer.example.com

SERVER_PROVIDER_PORT = 443
SERVER_PROVIDER_HOST_NAME = provider01.vddpi
PRIVATE_CA = registry01.vddpi:8001

CONSUMER_DIR_NAME ?= consumer

MODE ?= demo# eval-01

ifneq ($(strip $(EXPERIMENT_CONTAINER_NAME)),)
ENV_EXPERIMENT := EXPERIMENT_CONTAINER_NAME=$(EXPERIMENT_CONTAINER_NAME)
endif

.PHONY: gramine-base
gramine-base:
	@echo "Building gramine-base:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.graminebase docker \
		-t gramine-base:latest

load-gramine-base:
	@bash ./load_gramine_base.sh

.PHONY: gramine-consumer
gramine-consumer: load-gramine-base
	@echo "Building gramine-consumer:latest (mode:$(MODE))"
	@if [ "$(MODE)" = "eval-01" ]; then \
		$(DOCKER_CMD) build -f docker/Dockerfile.gramineconsumer docker \
		--build-arg CODE=code_eval_01 \
		-t gramine-consumer:latest; \
	elif [ "$(MODE)" = "eval-02" ]; then \
		$(DOCKER_CMD) build -f docker/Dockerfile.gramineconsumer docker \
		--build-arg CODE=code_eval_02 \
		-t gramine-consumer:latest; \
	elif [ "$(MODE)" = "eval-03" ]; then \
		$(DOCKER_CMD) build -f docker/Dockerfile.gramineconsumer docker \
		--build-arg CODE=code_eval_03 \
		-t gramine-consumer:latest; \
	else \
		$(DOCKER_CMD) build -f docker/Dockerfile.gramineconsumer docker \
		-t gramine-consumer:latest; \
	fi

.PHONY: consumer-benchmark-nosgx
consumer-benchmark-nosgx:
	@echo "Building consumer-benchmark-nosgx:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.consumer.benchmark.nosgx docker \
		-t consumer-benchmark-nosgx:latest

.PHONY: run-consumer-benchmark-nosgx
run-consumer-benchmark-nosgx: consumer-benchmark-nosgx
	@echo "Running consumer-benchmark-nosgx:latest"
	@cd consumer_benchmark_nosgx && \
		$(DOCKER_COMPOSE_CMD) up

.PHONY: stop-consumer-benchmark-nosgx
stop-consumer-benchmark-nosgx: consumer-benchmark-nosgx
	@cd consumer_benchmark_nosgx && \
		$(DOCKER_COMPOSE_CMD) down

gramine-consumer-mrenclave:
	@$(DOCKER_CMD) run -it --rm --entrypoint gramine-sgx-sigstruct-view gramine-consumer:latest python.sig

.PHONY: gramine-registry
gramine-registry: gramine-base
	@echo "Building gramine-registry:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.gramineregistry docker \
	-t gramine-registry:latest

.PHONY: db-provider
db-provider:
	@echo "Building db-provider"
	@$(DOCKER_CMD) build -f docker/Dockerfile.dbprovider docker \
	-t db-provider:latest

.PHONY: provider
provider:
	@echo "Building server-provider:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.provider docker \
	-t server-provider:latest

.PHONY: analyzer-registry
analyzer-registry:
	@echo "Building analyzer-registry:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.analyzer docker \
	-t analyzer-registry:latest

.PHONY: ca-registry
ca-registry:
	@echo "Building ca-registry:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.ca docker \
	-t ca-registry:latest

.PHONY: api-registry
api-registry:
	@echo "Building api-registry:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.apiregistry docker \
	-t api-registry:latest

.PHONY: datatype-api
datatype-api:
	@echo "Building Datatype API"
	@$(DOCKER_CMD) build -f docker/Dockerfile.datatype docker \
	-t datatype-api:latest

.PHONY: psuedo-ias
psuedo-ias:
	@echo "Building psuedo-ias:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.ias docker \
	-t psuedo-ias:latest

.PHONY: psuedo-api
psuedo-api:
	@echo "Building psuedo-api:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.api docker \
	-t psuedo-api:latest

# Consumer
.PHONY: run-consumer
run-consumer: gramine-consumer
	@cd $(CONSUMER_DIR_NAME) && \
	SPID=$(SPID) \
	IS_LINKABLE=$(IS_LINKABLE) \
	PRIVATE_CA=$(PRIVATE_CA) \
	IAS_SUBSCRIPTION_KEY=$(IAS_SUBSCRIPTION_KEY) \
	COUNTRY=$(COUNTRY_CONSUMER) \
	CNAME=$(CNAME_CONSUMER) \
	CONSUMER_HOST_NAME=$(CNAME_CONSUMER) \
	$(ENV_EXPERIMENT) $(DOCKER_COMPOSE_CMD) up -d

.PHONY: stop-consumer
stop-consumer:
	@cd $(CONSUMER_DIR_NAME) && \
	SPID=$(SPID) \
	IS_LINKABLE=$(IS_LINKABLE) \
	PRIVATE_CA=$(PRIVATE_CA) \
	IAS_SUBSCRIPTION_KEY=$(IAS_SUBSCRIPTION_KEY) \
	COUNTRY=$(COUNTRY_CONSUMER) \
	CNAME=$(CNAME_CONSUMER) \
	CONSUMER_HOST_NAME=$(CNAME_CONSUMER) \
	$(ENV_EXPERIMENT) $(DOCKER_COMPOSE_CMD) down

# Provider
.PHONY: run-provider
run-provider: db-provider provider
	@cd provider && \
	SERVER_PORT=$(SERVER_PROVIDER_PORT) \
	SERVER_HOST_NAME=$(SERVER_PROVIDER_HOST_NAME) \
	PRIVATE_CA=$(PRIVATE_CA) \
	$(DOCKER_COMPOSE_CMD) up -d

.PHONY: stop-provider
stop-provider:
	@cd provider && \
	SERVER_PORT=$(SERVER_PROVIDER_PORT) \
	SERVER_HOST_NAME=$(SERVER_PROVIDER_HOST_NAME) \
	PRIVATE_CA=$(PRIVATE_CA) \
	$(DOCKER_COMPOSE_CMD) down

.PHONY: run-registry
run-registry:
	$(MAKE) run-registry-network
	$(MAKE) run-registry-service

.PHONY: run-registry-service
run-registry-service: gramine-registry analyzer-registry ca-registry api-registry datatype-api psuedo-ias psuedo-api
	@cd registry && $(DOCKER_COMPOSE_CMD) up --build -d
	@cd registry && ./connect_registry_network.sh

.PHONY: restart-registry-service
restart-registry-service:
	@cd registry && $(DOCKER_COMPOSE_CMD) down
	@cd registry && $(DOCKER_COMPOSE_CMD) up -d

.PHONY: run-registry-network
run-registry-network:
	@cd registry && ./fablo generate fablo-config.json
	@echo "COMPOSE_PROJECT_NAME=fablo_network" >> registry/fablo-target/fabric-docker/.env
	@cd registry && ./fablo up fablo-config.json
	@cd init && sleep 5 && ./registry_setup.sh

.PHONY: stop-registry
stop-registry:
	@cd registry && ./fablo down
	@cd registry && $(DOCKER_COMPOSE_CMD) down
	@cd registry && ./fablo prune

.PHONY: restart-registry
restart-registry:
	@$(MAKE) stop-registry
	@$(MAKE) run-registry

.PHONY: clean
clean:
	@echo "Removing images"
	@$(DOCKER_CMD) rmi gramine-base:latest \
	gramine-consumer:latest \
	gramine-registry:latest \
	db-provider:latest \
	server-provider:latest \
	analyzer-registry:latest \
	ca-registry:latest \
	api-registry:latest \
	psuedo-ias:latest \
	datatype-api:latest \
	psuedo-api:latest
