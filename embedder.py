from ingestion import extract_pages, chunk_pages
from sentence_transformers import SentenceTransformer

model=SentenceTransformer("all-MiniLM-L6-v2")

chunks=chunk_pages(extract_pages("constitution.pdf"))
texts=[c["text"] for c in chunks]
vectors=model.encode(texts)
