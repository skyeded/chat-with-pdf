from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.agents.workflow import graph

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello" : "World"}

class APIInput(BaseModel):
    topic: str = Field(description="Input topic for Chatbot.")

@app.post("/chat")
def chat(input: APIInput):
    response = graph.invoke({"messages": [
        {"role" : "user",
         "content" : input.topic}
    ]},
    {"recursion_limit": 100})

    return response

