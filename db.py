import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")

def get_collection():
    return client.get_or_create_collection("constitution")

def search(query, n_results=3):
    collection = get_collection()
    query_vector = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results
    )
    return results["documents"][0]