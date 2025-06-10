#!/bin/sh
export QDRANT_STORAGE_DIR=./qdrant_storage
export FASTMCP_TRANSPORT=stdio
cd "$(dirname "$0")"

podman machine list --format '{{.Running}}' | grep -q true || podman machine start

cleanup() {
    podman compose down >/dev/null 2>&1
}

trap cleanup EXIT INT TERM

podman compose up -d >/dev/null 2>&1

CONTAINER_ID=$(podman ps --filter "label=com.docker.compose.service=qdrant-mcp-server" --format "{{.ID}}" 2>/dev/null)

exec podman attach "$CONTAINER_ID"
