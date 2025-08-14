from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.agents.workflow import graph, clear_memory_func, checkpointer

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello" : "World"}

class APIInput(BaseModel):
    topic: str = Field(description="Input topic for Chatbot.")

class CMInput(BaseModel):
    clear_memory: str = Field(description="For clearing memory from a single session.")

@app.post("/chat")
def chat(input: APIInput):
    response = graph.invoke({"messages": [
        {"role" : "user",
         "content" : input.topic},
    ]},
    config={"recursion_limit" : 25, "thread_id" : "user123"})

    return response["messages"][-1].content.split("FINAL ANSWER: ")[-1]

@app.post("/clear_memory")
def clear_memory(input: CMInput):
    if input.clear_memory == "clear":
        clear_memory_func(checkpointer, "user123")
        return {"status" : "memory cleared"}
    elif input.clear_memory == "show":
        config = {"configurable": {"thread_id": "user123"}}
        state_snapshot = graph.get_state(config)
        return {"status" : "show message history",
                "state" : state_snapshot}
    else:
        return {"status" : "unknown command"}

