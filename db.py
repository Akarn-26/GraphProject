import os
from dotenv import load_dotenv
from pinecone import Pinecone
from fastembed import TextEmbedding

load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("constitution")
model = TextEmbedding("BAAI/bge-small-en-v1.5")

def store(chunks, vectors):
    items = []
    for chunk, vector in zip(chunks, vectors):
        items.append({
            "id": chunk["chunk_id"],
            "values": list(vector),
            "metadata": {
                "text": chunk["text"],
                "page_number": chunk["page_number"],
                "source": chunk["source"]
            }
        })
    index.upsert(vectors=items)
    print(f"Stored {len(items)} vectors")

def search(query, n_results=3):
    query_vector = list(model.embed([query]))[0].tolist()
    results = index.query(
        vector=query_vector,
        top_k=n_results,
        include_metadata=True
    )
    return [match["metadata"]["text"] for match in results["matches"]]

if __name__ == "__main__":
    from ingestion import extract_pages, chunk_pages
    chunks = chunk_pages(extract_pages("constitution.pdf"))
    vectors = list(model.embed([c["text"] for c in chunks]))
    store(chunks, vectors)