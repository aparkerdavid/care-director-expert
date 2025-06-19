#!/bin/sh
echo "PROCESS DOCS AND CODE"
# uv run python /app/process_documents.py & uv run python /app/process_code.py & wait
uv run python ./process_documents.py & uv run python ./process_code.py & wait
