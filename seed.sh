#!/bin/sh
export QDRANT_STORAGE_DIR=./qdrant_storage
export FASTMCP_TRANSPORT=stdio
cd "$(dirname "$0")"
export COMPOSE_FILE="./docker-compose-seed.yml"

podman machine list --format '{{.Running}}' | grep -q true || podman machine start

cleanup() {
    podman compose --file $COMPOSE_FILE down >/dev/null 2>&1
}

trap cleanup EXIT INT TERM

podman compose --file $COMPOSE_FILE up 

