#!/usr/bin/env python3
"""
Code processing script using LlamaIndex with tree-sitter language detection.
Processes code files and stores them in Qdrant vector database.
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, List
from qdrant_client import QdrantClient
from qdrant_client import models
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.node_parser import CodeSplitter, SentenceSplitter
import tree_sitter_language_pack


def load_language_mappings() -> Dict[str, List[str]]:
    """Load language mappings from JSON file."""
    with open('language-mappings.json', 'r') as f:
        return json.load(f)


def get_language_from_extension(file_path: str, language_mappings: Dict[str, List[str]]) -> Optional[str]:
    """Determine programming language from file extension."""
    file_extension = Path(file_path).suffix.lower()
    
    for language, extensions in language_mappings.items():
        if file_extension in extensions:
            return language
    
    return None


def process_code(code_path: str, collection_name: str) -> None:
    """Process code files and store in Qdrant. Rebuilds collection from scratch."""
    
    # use FastEmbed (same as MCP server)
    Settings.embed_model = FastEmbedEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Load language mappings
    try:
        language_mappings = load_language_mappings()
    except Exception as e:
        print(f"Failed to load language mappings: {e}")
        return None
    
    # Get Qdrant connection details from environment variables with defaults
    qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
    qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))
    
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        collections = client.get_collections()
        print(f"Connected to Qdrant successfully at {qdrant_host}:{qdrant_port}")
    except Exception as e:
        print(f"Failed to connect to Qdrant at {qdrant_host}:{qdrant_port}: {e}")
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

    if not os.path.exists(code_path):
        print(f"Creating code directory: {code_path}")
        os.makedirs(code_path)
        print(f"Please add code files to {code_path} and run again.")
        return

    print(f"Loading code files from {code_path}...")
    documents = SimpleDirectoryReader(input_dir=code_path, recursive=True).load_data()

    if not documents:
        print(f"No code files found in {code_path}")
        return

    print(f"Loaded {len(documents)} code files")

    print("Processing code files and storing embeddings...")
    all_nodes = []
    
    for doc in documents:
        file_path = doc.metadata.get('file_path', '')
        language = get_language_from_extension(file_path, language_mappings)
        
        if language is None:
            print(f"Skipping unsupported file: {file_path}")
            continue
            
        try:
            # Test if tree-sitter parser is available for this language
            tree_sitter_language_pack.get_parser(language)
            
            # Use CodeSplitter for supported languages
            node_parser = CodeSplitter.from_defaults(
                language=language,
                chunk_lines=40,
                chunk_lines_overlap=15,
                max_chars=1500
            )
            nodes = node_parser.get_nodes_from_documents([doc])
            print(f"Processed {file_path} ({language}): {len(nodes)} chunks")
            
        except Exception as e:
            print(f"CodeSplitter failed for {file_path} ({language}): {e}")
            print(f"Falling back to SentenceSplitter for {file_path}")
            
            # Fallback to SentenceSplitter for unsupported languages
            node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
            nodes = node_parser.get_nodes_from_documents([doc])
            
        all_nodes.extend(nodes)
    
    if not all_nodes:
        print("No processable code files found")
        return
    
    print(f"Created {len(all_nodes)} total chunks")
    
    try:
        # Extract texts for batch embedding
        texts = [node.text for node in all_nodes]
        
        # Generate embeddings in batch (much faster than sequential)
        embeddings = Settings.embed_model.get_text_embedding_batch(texts)
        
        # Create points
        points = []
        for i, (node, embedding) in enumerate(zip(all_nodes, embeddings)):
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

        print(f"Loading chunks into Qdrant collection '{collection_name}'")
        
        # Batch upsert to avoid timeouts
        batch_size = 1000
        total_points = len(points)
        
        for i in range(0, total_points, batch_size):
            batch = points[i:i + batch_size]
            client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=False
            )
            print(f"Uploaded batch {i//batch_size + 1}/{(total_points + batch_size - 1)//batch_size} ({len(batch)} points)")
        
        print(f"Successfully stored {total_points} chunks")

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

    print(f"Successfully processed and stored code files in Qdrant collection '{collection_name}'")


if __name__ == "__main__":
    import sys
    
    code_path = sys.argv[1] if len(sys.argv) > 1 else "./code"
    collection_name = sys.argv[2] if len(sys.argv) > 2 else "code"
    
    process_code(code_path, collection_name)
