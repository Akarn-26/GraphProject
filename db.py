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

print(f"Stored {collection.count()} chunks in ChromaDB")

query = "What are the powers of the King?"
query_vector = model.encode(query).tolist()

results = collection.query(
    query_embeddings=[query_vector],
    n_results=3
)

for i, doc in enumerate(results["documents"][0]):
    print(f"--- Result {i+1} ---")
    print(doc)
    print(results["metadatas"][0][i])