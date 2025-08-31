#!/bin/bash

# set -x

if [ $# -ne 3 ]; then
	cat <<- _EOS_
		Usage:
		  "$0" <registry_ip> <consumer_ip> <provider_ip>

		Description:
		  This script generates \`.env\` files for three services (registry, consumer, provider).
		  Each \`.env\` file will be created in its corresponding subdirectory:
		    - ./registry/.env
		    - ./consumer/.env
		    - ./provider/.env

		  The generated \`.env\` file contains the following environment variables:
		    REGISTRY_IP   - IP address (or hostname) of the registry service
		    CONSUMER_IP   - IP address (or hostname) of the consumer service
		    PROVIDER_IP   - IP address (or hostname) of the provider service

		Arguments:
		  <registry_ip>   IP address or hostname for registry01.vddpi
		  <consumer_ip>   IP address or hostname for consumer01.vddpi
		  <provider_ip>   IP address or hostname for provider01.vddpi

		Example:
		  "$0" 192.168.220.5 192.168.220.6 192.168.220.7

		  → creates:
		      ./registry/.env
		      ./consumer/.env
		      ./provider/.env

		  with content like:
		      REGISTRY_IP=192.168.220.5
		      CONSUMER_IP=192.168.220.6
		      PROVIDER_IP=192.168.220.7
	_EOS_
	exit 1
fi

registry_addr="$1"
consumer_addr="$2"
provider_addr="$3"

function gen_env_file() {
	cat > $1/.env <<-_EOS_
		REGISTRY_IP=$2
		CONSUMER_IP=$3
		PROVIDER_IP=$4
	_EOS_
}

gen_env_file ./registry $registry_addr $consumer_addr $provider_addr
gen_env_file ./consumer $registry_addr $consumer_addr $provider_addr
gen_env_file ./provider $registry_addr $consumer_addr $provider_addr

echo "OK"

cat <<- _EOS_
	✅ .env files generated successfully.

	👉 Please add the following lines to your /etc/hosts on this machine:
	$registry_addr registry01.vddpi
	$consumer_addr consumer01.vddpi
	$provider_addr provider01.vddpi
_EOS_
