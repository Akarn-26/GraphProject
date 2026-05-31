# 🏛️ Constitution Knowledge Graph QA

A hybrid AI system that answers questions about the Norwegian Constitution using both a **knowledge graph** (Neo4j) and **semantic vector search** (Pinecone). Questions are intelligently routed to the right retrieval strategy — graph traversal for specific facts, vector search for summaries, or both combined.

---

## What makes this different from plain RAG?

Most RAG (Retrieval Augmented Generation) systems just embed documents and search by similarity. That works well for broad questions but struggles with precise factual queries like *"which article grants freedom of speech?"* — because cosine similarity finds semantically close text, not exact graph relationships.

This system adds a **knowledge graph layer** on top. Every entity (King, Parliament, Article 100) and relationship (GRANTS, RESTRICTS, HAS_POWER) is stored as a structured triple in Neo4j. When a question needs a precise fact, the system generates a Cypher query and retrieves the exact answer from the graph — no hallucination, no approximation.

The result: fact-based questions get graph-precise answers, summary questions get semantically rich answers, and complex questions get both merged together.

---

## Architecture

```
PDF
 └─ pdfplumber extraction
     └─ text cleaning
         └─ recursive chunking (700 chars, 80 overlap)
             ├─ sentence-transformers embedding → Pinecone (vector search)
             └─ Groq LLM extraction → triples → Neo4j (graph search)

User question
 └─ Groq LLM router (graph / summary / both)
     ├─ graph  → Groq generates Cypher → Neo4j → answer
     ├─ summary → embed question → Pinecone top-3 chunks → answer
     └─ both   → graph + vector results merged → answer
```

---

## Project structure

```
graph_project/
├── ingestion.py          # PDF parsing, cleaning, chunking
├── extractor.py          # LLM-based triple extraction → triples.txt
├── neo4j_writer.py       # writes triples to Neo4j
├── db.py                 # Pinecone vector store (store + search)
├── router.py             # query classification + answer synthesis
├── main.py               # FastAPI backend
├── app.py                # Streamlit frontend
├── constitution.pdf      # source document
├── triples.txt           # extracted knowledge graph triples
├── requirements.txt
├── Dockerfile
└── .env
```

---

## Stage by stage breakdown

### Stage 1a — PDF parsing and text cleaning (`ingestion.py`)

**Why not just `open()` the PDF?**
A PDF is not a text file. It is a set of drawing instructions — every character has an (x, y) coordinate on a page. `pdfplumber` reconstructs reading order from those coordinates and returns a string per page.

Raw extraction is noisy. Three types of noise were handled:

**1. Corrupted characters** — the PDF contained `(cid:127)` wherever a bullet point symbol appeared. This is a common artifact when a PDF uses a custom font that the parser cannot decode. It was stripped with a simple `str.replace`.

**2. Repeating headers and footers** — every page had `Norway 1814 (rev.2015)` and `constituteproject.org` injected by the PDF generator. These add noise to every chunk and mislead the embedding model. They were stripped using a combined rule: if a line is shorter than 60 characters AND contains a known noise string, remove it. The length check prevents accidentally removing a real sentence that happens to mention "Norway 1814".

**3. Page number lines** — lines containing only `Page N` were removed the same way.

The result is clean, continuous prose per page — ready for chunking.

---

### Stage 1b — Chunking

**Why chunk at all?**
An embedding model compresses a piece of text into a single vector. If that text is too long, too much meaning gets averaged together and the vector becomes a blurry representation of everything — useful for nothing specific. Each chunk should represent one coherent idea.

**Recursive character splitting** was used with these parameters:
- `chunk_size = 700` characters (~120 words)
- `chunk_overlap = 80` characters

The splitter tries to cut at `\n\n` (paragraph breaks) first, then `\n`, then `.`, then spaces — always at the most natural boundary. The 80-character overlap ensures a sentence that spans a chunk boundary appears in both chunks, so context is never completely lost.

Each chunk carries metadata: `chunk_id`, `source`, `page_number`, and the text itself. This metadata travels through the entire pipeline and appears in the final answer as a citation.

---

### Stage 2 — Embeddings and vector store (`db.py`)

**What is an embedding?**
The sentence `"The King holds executive power"` is converted by `all-MiniLM-L6-v2` into a 384-dimensional float vector like `[0.02, -0.87, 0.41, ...]`. This vector is a coordinate in high-dimensional semantic space. Sentences with similar meaning end up at nearby coordinates — even if the words are completely different.

**Why cosine similarity over euclidean distance?**
Cosine measures the angle between two vectors, not the straight-line distance. A short sentence and a long paragraph about the same topic would be far apart in euclidean space due to length difference, but nearly identical in cosine similarity because they point in the same semantic direction.

**Why Pinecone over local ChromaDB?**
ChromaDB stores vectors on local disk. On cloud deployment (Render), the filesystem resets on every restart — all vectors would be lost. Pinecone is a managed cloud vector database. Vectors are stored once and persist permanently regardless of server restarts or redeployments.

**Accuracy vs plain embedding search**
Pure vector search returns semantically similar chunks — good for summaries, poor for precise facts. Asking *"which article restricts the King?"* returns chunks about the King, but may miss the specific article if the wording differs. The knowledge graph solves this by storing the explicit relationship `Article X -RESTRICTS-> King` as a structured fact — no similarity approximation, exact match.

---

### Stage 3 — Knowledge graph extraction (`extractor.py`, `neo4j_writer.py`)

**What is a triple?**
Every fact is stored as three parts: subject → relationship → object. Example: `King -HAS_POWER-> Executive Power`. The entire knowledge graph is a collection of these triples.

**Why a canonical schema?**
Without a fixed schema, the LLM invents different labels every time — "monarch", "the King", "Norwegian King" all become separate nodes for the same entity. A canonical schema forces consistency:

- Node types: `Person, Role, Institution, Right, Duty, Article`
- Relationship types: `HAS_POWER, PART_OF, DEFINED_IN, APPOINTED_BY, RESPONSIBLE_TO, GRANTS, RESTRICTS`

The LLM is instructed to use only these labels. This makes the graph queryable — you can ask for all `Person` nodes with `HAS_POWER` relationships and get consistent results.

**Source article tracking**
Each triple also stores `source_article` — the article number where the fact was stated. This is written as a property on the relationship in Neo4j, enabling queries like *"show me all facts from Article 49"*.

**Why Groq Llama 3.3 70b?**
Smaller models (8b) frequently deviate from the JSON format or invent node types outside the schema. The 70b model follows structured output instructions reliably enough for production use.

---

### Stage 4 — Query routing (`router.py`)

The LLM classifies every incoming question into one of three routes:

- `graph` — specific entities, facts, powers, rights, article references
- `summary` — broad overviews, explanations, general understanding
- `both` — needs precise facts AND contextual explanation

A few-shot prompt with examples guides the classification. Without examples, smaller models default to `summary` for almost everything.

---

### Stage 5 — Answer synthesis (`router.py`)

**Graph path**: Groq generates a Cypher query from the question using the schema as context. The query runs against Neo4j and returns structured results. Those results are passed to Groq for synthesis into a readable answer.

**Summary path**: The question is embedded and Pinecone returns the top 3 most similar chunks. Those chunks are passed to Groq as context for answer generation.

**Both path**: Graph results and vector chunks are merged into one context string and synthesized together — the graph provides the precise skeleton, the vector chunks provide the surrounding narrative.

---

## Setup

### Prerequisites
- Python 3.11+
- Neo4j AuraDB account (free) — [neo4j.com/cloud/aura-free](https://neo4j.com/cloud/aura-free)
- Pinecone account (free) — [pinecone.io](https://pinecone.io)
- Groq API key (free) — [console.groq.com](https://console.groq.com)

### Installation

```bash
git clone https://github.com/your-repo/constitution-kg
cd constitution-kg
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file:

```
GROQ_API_KEY=your_groq_key
NEO4J_URI=neo4j+s://your-aura-instance.databases.neo4j.io
NEO4J_PASSWORD=your_password
PINECONE_API_KEY=your_pinecone_key
```

### One-time data pipeline

Run these once to populate the databases:

```bash
# extract triples and store to triples.txt
python extractor.py

# write triples to Neo4j
python neo4j_writer.py

# embed chunks and store to Pinecone
python db.py
```

### Running locally

```bash
# terminal 1 — FastAPI backend
uvicorn main:app --reload

# terminal 2 — Streamlit frontend
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Deployment (Render)

Two web services on [render.com](https://render.com):

**Service 1 — FastAPI backend**
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Environment variables: all four from `.env` above

**Service 2 — Streamlit frontend**
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.port 8000 --server.address 0.0.0.0`
- Environment variables: `API_URL=https://your-fastapi-service.onrender.com`

---

## Canonical schema reference

| Node type | Examples |
|---|---|
| Person | King, Prime Minister |
| Role | Executive Power, Legislative Power |
| Institution | Council of State, Storting, Supreme Court |
| Right | Freedom of Speech, Right to Vote |
| Duty | Military Service, Tax Obligation |
| Article | Article 1, Article 100 |

| Relationship | Meaning |
|---|---|
| HAS_POWER | entity holds a power |
| PART_OF | entity belongs to a body |
| DEFINED_IN | concept defined in an article |
| APPOINTED_BY | entity appointed by another |
| RESPONSIBLE_TO | entity accountable to another |
| GRANTS | article grants a right or power |
| RESTRICTS | article limits a power |

---

## Tech stack

| Component | Technology |
|---|---|
| PDF parsing | pdfplumber |
| Text splitting | LangChain RecursiveCharacterTextSplitter |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector store | Pinecone |
| Knowledge graph | Neo4j AuraDB |
| LLM | Groq (Llama 3.3 70b) |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Deployment | Render |
