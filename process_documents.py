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
    
    # use FastEmbed (same as MCP server)
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
    

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            # Qdrant MCP server requires this specific vector name!
            "fast-all-minilm-l6-v2": models.VectorParams(size=384, distance=models.Distance.COSINE)
        }
    )

    if not os.path.exists(docs_path):
        print(f"Creating documents directory: {docs_path}")
        os.makedirs(docs_path)
        print(f"Please add documents to {docs_path} and run again.")
        return

    print(f"Loading documents from {docs_path}...")
    documents = SimpleDirectoryReader(input_dir=docs_path, recursive=True).load_data()

    if not documents:
        print(f"No documents found in {docs_path}")
        return

    print(f"Loaded {len(documents)} documents")

    print("Processing documents and storing embeddings...")
    try:
        from llama_index.core.node_parser import SentenceSplitter
        
        node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = node_parser.get_nodes_from_documents(documents)
        print(f"Created {len(nodes)} chunks")
        
        points = []
        for i, node in enumerate(nodes):

            embedding = Settings.embed_model.get_text_embedding(node.text)
            
            # Qdrant MCP server requires this payload format
            payload = {
                "document": node.text,
                "metadata": {
                    "file_path": node.metadata.get("file_path", ""),
                    "file_name": node.metadata.get("file_name", ""),
                    "chunk_id": str(i),
                    "node_id": node.node_id,
                }
            }
            
            points.append(models.PointStruct(
                id=node.node_id,
                vector={"fast-all-minilm-l6-v2": embedding},
                payload=payload
            ))

        print(f"Loading chunks into Qdrant collection 'documents'")
        
        client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True
        )
        print(f"Successfully stored {len(points)} chunks")

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

if __name__ == "__main__":
    import sys
    
    docs_path = sys.argv[1] if len(sys.argv) > 1 else "./documents"
    collection_name = sys.argv[2] if len(sys.argv) > 2 else "documents"
    
    process_documents(docs_path, collection_name)
