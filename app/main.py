from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.agents.workflow import graph, clear_memory_func, checkpointer

app = FastAPI()

# initialize endpoint
@app.get("/")
def read_root():
    return {"Hello" : "World"}

# class for communicating with chatbot
class APIInput(BaseModel):
    topic: str = Field(description="Input topic for Chatbot.")

# class for clearing memory or show message_history
class CMInput(BaseModel):
    clear_memory: str = Field(description="For clearing memory from a single session.")

# for communicating with chatbot
@app.post("/chat")
def chat(input: APIInput):
    response = graph.invoke({"messages": [
        {"role" : "user",
         "content" : input.topic},
    ]},
    config={"recursion_limit" : 25, "thread_id" : "user123"})

    return response["messages"][-1].content.split("FINAL ANSWER: ")[-1]

# for clearing memory or show message_history
@app.post("/clear_memory")
def clear_memory(input: CMInput):
    if input.clear_memory == "clear": # clear if {"input" : "clear"}
        clear_memory_func(checkpointer, "user123")
        return {"status" : "memory cleared"}
    elif input.clear_memory == "show": # show if {"input" : "show"}
        config = {"configurable": {"thread_id": "user123"}}
        state_snapshot = graph.get_state(config)
        return {"status" : "show message history",
                "state" : state_snapshot}
    else:
        return {"status" : "unknown command"}

