from fastapi import FastAPI, Request
from pydantic import BaseModel
from router import handle_query
from sentence_transformers import SentenceTransformer
from contextlib import asynccontextmanager
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.st_model=SentenceTransformer("all-MiniLM-L6-v2")
    app.state.driver=GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=("neo4j", os.getenv("NEO4J_PASSWORD"))
    )
    app.state.ready = True
    print("Model and DB loaded")
    yield
    app.state.driver.close()

app=FastAPI(lifespan=lifespan)
class UserQuery(BaseModel):
    query:str

@app.get("/health")
def health(request:Request):
    ready=getattr(request.app.state,"ready",False)
    return {"status":"ready" if ready else "loading"}

@app.post("/query")
def answer_query(user_query: UserQuery, request: Request):
    message = handle_query(
        user_query.query,
        request.app.state.driver,
        request.app.state.st_model
    )
    return {"Answer": message}