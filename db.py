import chromadb
from embedder import vectors, chunks,model
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("constitution")

collection.add(
    ids=[c["chunk_id"] for c in chunks],
    documents=[c["text"] for c in chunks],
    embeddings=vectors.tolist(),
    metadatas=[{"page_number": c["page_number"], "source": c["source"]} for c in chunks]
)

