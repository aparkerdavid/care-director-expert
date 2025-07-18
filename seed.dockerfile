FROM python:3.11-slim

WORKDIR /app

# Install uv for package management
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv venv
RUN uv pip install -e .

RUN touch /bin/seed
RUN chmod +x /bin/seed
RUN echo '#!/bin/sh\n' >> /bin/seed
RUN echo 'uv run python /app/process_documents.py & uv run python /app/process_code.py & wait' >> /bin/seed

# Set environment variables with defaults that can be overridden at runtime
ENV QDRANT_HOST="qdrant"
ENV QDRANT_PORT="6333"
ENV COLLECTION_NAME="documents"
ENV FASTMCP_DEBUG="true"
ENV FASTMCP_LOG_LEVEL="INFO"
ENV EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"

CMD ["/bin/seed"]
