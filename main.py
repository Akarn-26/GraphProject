from fastapi import FastAPI, Request
from pydantic import BaseModel
from router import handle_query
from contextlib import asynccontextmanager
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
load_dotenv()

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.driver=GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=("d4c48bc9", os.getenv("NEO4J_PASSWORD"))
    )
    app.state.ready = True
    print("DB loaded")
    yield
    app.state.driver.close()
app=FastAPI(lifespan=lifespan)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "trace": traceback.format_exc()}
    )
class UserQuery(BaseModel):
    query:str
@app.head("/health")
def health():
    return {} #for uptime robot head is equivalent to ping
@app.get("/")
def home():
    return {"Message":"Welcome to Neo4j graph Project"}
@app.get("/health")
def health(request:Request):
    ready=getattr(request.app.state,"ready",False)
    return {"status":"ready" if ready else "loading"}

@app.post("/query")
def answer_query(user_query: UserQuery, request: Request):
    message = handle_query(
        user_query.query,
        request.app.state.driver
    )
    return {"Answer": message}