#!/usr/bin/env python3
"""
Document processing script using LlamaIndex with sensible defaults.
Processes documents and stores them in Qdrant vector database.
"""

import os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client import models
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore


def process_documents(docs_path: str = "./documents", collection_name: str = "documents"):
    """Process documents and store in Qdrant. Rebuilds collection from scratch."""
    
    # Configure LlamaIndex to use FastEmbed (same as MCP server)
    Settings.embed_model = FastEmbedEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    try:
        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        print(f"Connected to Qdrant successfully")
    except Exception as e:
        print(f"Failed to connect to Qdrant: {e}")
        return None
    
    collection_names = [c.name for c in collections.collections]
    if collection_name in collection_names:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection '{collection_name}'")
    else:
        print(f"Collection '{collection_name}' doesn't exist yet")
    

    # Create collection with named vector config to match MCP server expectations
    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "fast-all-minilm-l6-v2": models.VectorParams(size=384, distance=models.Distance.COSINE)
        }
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        dense_vector_name="fast-all-minilm-l6-v2"  # Override default "text-dense"
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
    try:
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
        )
        print(f"Index created successfully")

        # Check final state
        collections_after = client.get_collections()
        if collections_after.collections:
            for collection in collections_after.collections:
                info = client.get_collection(collection.name)
                print(f"Collection '{collection.name}' has {info.points_count} points")

    except Exception as e:
        print(f"Error creating index: {e}")
        import traceback
        traceback.print_exc()
        return None

    print(f"Successfully processed and stored {len(documents)} documents in Qdrant collection '{collection_name}'")
    return index


if __name__ == "__main__":
    import sys
    
    docs_path = sys.argv[1] if len(sys.argv) > 1 else "./documents"
    collection_name = sys.argv[2] if len(sys.argv) > 2 else "documents"
    
    process_documents(docs_path, collection_name)
