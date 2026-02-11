#!/bin/bash

IMAGE_NAME="gramine-base"
IMAGE_LABEL="latest"
PATH_IMAGE="./cache/$IMAGE_NAME.tar"
PATH_ID="./cache/$IMAGE_NAME.id"

type gunzip >/dev/null 2>&1 || { echo "gunzip not found"; exit 1; }

load_image() {
	echo "Loading image from registry01.vddpi"
	ssh -T registry01.vddpi "docker save $IMAGE_NAME:$IMAGE_LABEL | gzip -c" | gunzip | docker load
}

REMOTE_ID=$(ssh -T registry01.vddpi "docker images --no-trunc --quiet $IMAGE_NAME:$IMAGE_LABEL 2>/dev/null")
LOCAL_ID=$(docker images --no-trunc --quiet $IMAGE_NAME:$IMAGE_LABEL 2>/dev/null)

if [ -z "$REMOTE_ID" ]; then
	echo "Image not found on remote"
	exit 1
elif [ -z "$LOCAL_ID" ]; then
	echo "Image not found locally"
	load_image
elif [ "$REMOTE_ID" != "$LOCAL_ID" ]; then
	echo "Image changed"
	load_image
else
	echo "Image unchanged, skipping import"
fi

exit 0
