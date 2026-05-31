from fastapi import FastAPI
from pydantic import BaseModel
from router import handle_query

app=FastAPI()
class UserQuery(BaseModel):
    query:str

@app.post("/query")
def answer_query(user_query:UserQuery):
    message=handle_query(user_query.query)
    return {"Answer":message}

