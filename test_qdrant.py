#!/usr/bin/env python3
"""Test script to check Qdrant contents."""

from qdrant_client import QdrantClient
from llama_index.embeddings.fastembed import FastEmbedEmbedding

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Get collection info
collection_info = client.get_collection("documents")
print(f"Collection 'documents' has {collection_info.points_count} points")
print(f"Vectors config: {collection_info.config.params.vectors}")

# Scroll through all points to see what's stored
points = client.scroll(
    collection_name="documents",
    limit=10,
    with_payload=True,
    with_vectors=False
)

print("\nStored documents:")
for point in points[0]:
    print(f"\nID: {point.id}")
    if point.payload:
        for key, value in point.payload.items():
            print(f"  {key}: {value[:100] if isinstance(value, str) and len(value) > 100 else value}")

# Test semantic search
print("\n\nTesting semantic search...")
embed_model = FastEmbedEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
query_embedding = embed_model.get_query_embedding("test query")

search_result = client.search(
    collection_name="documents",
    query_vector=("fast-all-minilm-l6-v2", query_embedding),
    limit=2
)

print(f"\nSearch returned {len(search_result)} results")
for result in search_result:
    print(f"\nScore: {result.score}")
    if result.payload:
        print(f"Payload: {result.payload}")