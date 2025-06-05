#!/usr/bin/env python3
"""
Launch script for the Qdrant MCP server with proper configuration.
"""

import os
import subprocess
import sys
from pathlib import Path


def launch_mcp_server():
    """Launch the MCP server with our configuration."""
    
    # Get the script directory and venv path
    script_dir = Path(__file__).parent
    venv_bin = script_dir / ".venv" / "bin"
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "QDRANT_URL": "http://localhost:6333",
        "COLLECTION_NAME": "documents",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
        "FASTMCP_DEBUG": "true",
        "FASTMCP_LOG_LEVEL": "INFO",
        "PATH": f"{venv_bin}:{env.get('PATH', '')}"
    })
    
    # Get transport mode from command line args
    transport = "stdio"  # default
    if len(sys.argv) > 1:
        transport = sys.argv[1]
    
    print(f"Starting Qdrant MCP server with transport: {transport}")
    print(f"Qdrant URL: {env['QDRANT_URL']}")
    print(f"Collection: {env['COLLECTION_NAME']}")
    print(f"Embedding model: {env['EMBEDDING_MODEL']}")
    print("-" * 50)
    
    # Launch the MCP server
    cmd = ["mcp-server-qdrant", "--transport", transport]
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\nMCP server stopped")
    except subprocess.CalledProcessError as e:
        print(f"Error starting MCP server: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(launch_mcp_server())