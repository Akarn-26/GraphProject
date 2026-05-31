import os
from dotenv import load_dotenv
from pinecone import Pinecone
load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("constitution")

def store(chunks, vectors):
    items = []
    for chunk, vector in zip(chunks, vectors):
        items.append({
            "id": chunk["chunk_id"],
            "values": vector.tolist(),
            "metadata": {
                "text": chunk["text"],
                "page_number": chunk["page_number"],
                "source": chunk["source"]
            }
        })
    index.upsert(vectors=items)
    print(f"Stored {len(items)} vectors")

def search(query, model, n_results=3):
    query_vector = model.encode(query).tolist()
    results = index.query(
        vector=query_vector,
        top_k=n_results,
        include_metadata=True
    )
    return [match["metadata"]["text"] for match in results["matches"]]

if __name__ == "__main__":
    from ingestion import extract_pages, chunk_pages
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    chunks = chunk_pages(extract_pages("constitution.pdf"))
    vectors = model.encode([c["text"] for c in chunks])
    store(chunks, vectors)
