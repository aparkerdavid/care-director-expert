FROM python:3.11-slim

WORKDIR /app

# Install uv for package management
RUN pip install --no-cache-dir uv

# Install the mcp-server-qdrant package
RUN uv pip install --system --no-cache-dir mcp-server-qdrant

# Expose the default port for SSE transport
EXPOSE 8000

# Set environment variables with defaults that can be overridden at runtime
ENV QDRANT_URL="http://qdrant:6333"
ENV COLLECTION_NAME="documents"
ENV FASTMCP_DEBUG="true"
ENV FASTMCP_LOG_LEVEL="INFO"
ENV EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"

# Run the server with stdio transport by default, but allow override
CMD uvx mcp-server-qdrant --transport ${FASTMCP_TRANSPORT:-stdio}
