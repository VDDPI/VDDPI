DOCKER_CMD = docker
DOCKER_COMPOSE_CMD = docker compose

SPID = 1234567890abcdef1234567890abcdef
IS_LINKABLE = 0
IAS_SUBSCRIPTION_KEY = 1234567890abcdef1234567890abcdef
COUNTRY_CONSUMER = JP
CNAME_CONSUMER = consumer.example.com

SERVER_PROVIDER_PORT = 443
SERVER_PROVIDER_HOST_NAME = 172.24.30.207
PRIVATE_CA = 172.24.30.207:8001

REGISTRY_DOCKERCOMPOSE_TEMPLATE_FILE = registry/docker-compose_template.yml
REGISTRY_DOCKERCOMPOSE_FILE = registry/docker-compose.yml
SERVER_PROVIDER_HOST_NAME = 192.168.220.7
PRIVATE_CA = 192.168.220.5:8001

.PHONY: gramine-base
gramine-base:
	@echo "Building gramine-base:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.graminebase docker \
		-t gramine-base:latest

load-gramine-base:
	@bash ./load_gramine_base.sh

.PHONY: gramine-consumer
gramine-consumer: load-gramine-base
	@echo "Building gramine-consumer:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.gramineconsumer docker \
	-t gramine-consumer:latest

.PHONY: gramine-registry
gramine-registry: gramine-base
	@echo "Building gramine-registry:latest"
	@$(DOCKER_CMD) build -f docker/Dockerfile.gramineregistry docker \
	-t gramine-registry:latest

.PHONY: db-provider
db-provider:
	@echo "Building db-provider:latest"
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
	@cd consumer && \
	SPID=$(SPID) \
	IS_LINKABLE=$(IS_LINKABLE) \
	PRIVATE_CA=$(PRIVATE_CA) \
	IAS_SUBSCRIPTION_KEY=$(IAS_SUBSCRIPTION_KEY) \
	COUNTRY=$(COUNTRY_CONSUMER) \
	CNAME=$(CNAME_CONSUMER) \
	CONSUMER_HOST_NAME=$(CNAME_CONSUMER) \
	$(DOCKER_COMPOSE_CMD) up -d

.PHONY: run-consumer
stop-consumer:
	@cd consumer && \
	SPID=$(SPID) \
	IS_LINKABLE=$(IS_LINKABLE) \
	PRIVATE_CA=$(PRIVATE_CA) \
	IAS_SUBSCRIPTION_KEY=$(IAS_SUBSCRIPTION_KEY) \
	COUNTRY=$(COUNTRY_CONSUMER) \
	CNAME=$(CNAME_CONSUMER) \
	CONSUMER_HOST_NAME=$(CNAME_CONSUMER) \
	$(DOCKER_COMPOSE_CMD) down

# Provider
.PHONY: run-provider
run-provider: db-provider provider
	@curl $(PRIVATE_CA)/root-crt > provider/files/RootCA.pem
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
run-registry: gramine-registry analyzer-registry ca-registry api-registry datatype-api psuedo-ias psuedo-api
	@cd registry && ./fablo up fablo-config.json
	@docker network ls -f "name=fablo_network" --format '{{.Name}}' | \
	xargs -i sed -e "s/FABLO_NETWORK/{}/g" $(REGISTRY_DOCKERCOMPOSE_TEMPLATE_FILE) > $(REGISTRY_DOCKERCOMPOSE_FILE)
	@cd registry && \
	$(DOCKER_COMPOSE_CMD) up --build -d
	@cd registry && ./connect_registry_network.sh
	@cd init && ./registry_setup.sh
	@echo "Registry setup completed!"

.PHONY: stop-registry
stop-registry:
	@cd registry && ./fablo down
	@cd registry && \
		$(DOCKER_COMPOSE_CMD) down
	@cd registry && ./fablo prune

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
