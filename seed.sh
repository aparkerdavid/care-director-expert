#!/bin/sh
export QDRANT_STORAGE_DIR=./qdrant_storage
export FASTMCP_TRANSPORT=stdio
cd "$(dirname "$0")"
export PODMAN_COMPOSE_WARNING_LOGS=false
export COMPOSE_FILE="./docker-compose-seed.yml"
export QDRANT_COMPOSE_FILE="./docker-compose-qdrant-only.yml"

podman machine list --format '{{.Running}}' | grep -q true || podman machine start

# Check if Qdrant is already running
QDRANT_RUNNING=$(podman ps --format "{{.Names}}" | grep -E "qdrant" | head -1)
STARTED_QDRANT=false

if [ -z "$QDRANT_RUNNING" ]; then
    podman compose --file $QDRANT_COMPOSE_FILE up -d
    STARTED_QDRANT=true
    # Wait for Qdrant to be ready
    until podman logs $(podman ps --format "{{.Names}}" | grep qdrant | head -1) 2>&1 | grep -q "Qdrant gRPC listening on"; do
        sleep 1
    done
fi

cleanup() {
    # Only stop Qdrant if we started it (podman auto-cleans up process-documents)
    if [ "$STARTED_QDRANT" = "true" ]; then
        podman compose --file $QDRANT_COMPOSE_FILE down >/dev/null 2>&1
    fi
}

trap cleanup EXIT INT TERM

podman compose --file $COMPOSE_FILE up --abort-on-container-exit

