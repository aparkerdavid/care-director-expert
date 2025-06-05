#!/usr/bin/env python3
"""
Document processing script using LlamaIndex with sensible defaults.
Processes documents and stores them in Qdrant vector database.
"""

import os
from pathlib import Path
from qdrant_client import QdrantClient
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore


def process_documents(docs_path: str = "./documents", collection_name: str = "documents"):
    """Process documents and store in Qdrant. Rebuilds collection from scratch."""
    
    # Initialize Qdrant client (assumes running on localhost:6333)
    client = QdrantClient(host="localhost", port=6333)
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection '{collection_name}'")
    except Exception:
        print(f"Collection '{collection_name}' doesn't exist yet")
    
    # Create vector store (will create new collection)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
    )
    
    # Check if documents directory exists
    if not os.path.exists(docs_path):
        print(f"Creating documents directory: {docs_path}")
        os.makedirs(docs_path)
        print(f"Please add documents to {docs_path} and run again.")
        return
    
    # Load documents using LlamaIndex defaults
    print(f"Loading documents from {docs_path}...")
    documents = SimpleDirectoryReader(docs_path).load_data()
    
    if not documents:
        print(f"No documents found in {docs_path}")
        return
    
    print(f"Loaded {len(documents)} documents")
    
    # Create index with Qdrant vector store
    print("Creating index and storing embeddings...")
    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store,
    )
    
    print(f"Successfully processed and stored {len(documents)} documents in Qdrant collection '{collection_name}'")
    return index


if __name__ == "__main__":
    import sys
    
    docs_path = sys.argv[1] if len(sys.argv) > 1 else "./documents"
    collection_name = sys.argv[2] if len(sys.argv) > 2 else "documents"
    
    process_documents(docs_path, collection_name)