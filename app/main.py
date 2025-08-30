from fastapi import FastAPI
from pydantic import BaseModel, Field
import inspect
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
async def chat(input: APIInput):
    response = await graph.ainvoke({"messages": [ #use await for asynchronous call, changed invoke to ainvoke (asynchronously invoke)
        {"role" : "user",
         "content" : input.topic},
    ]},
    config={"recursion_limit" : 25, "thread_id" : "user123"})

    return response["messages"][-1].content.split("FINAL ANSWER: ")[-1]

# for clearing memory or show message_history
@app.post("/clear_memory")
async def clear_memory(input: CMInput):
    if input.clear_memory == "clear": # clear if {"input" : "clear"}
        clear_memory_func(checkpointer, "user123")
        return {"status" : "memory cleared"}
    elif input.clear_memory == "show": # show if {"input" : "show"}
        config = {"configurable": {"thread_id": "user123"}}
        state_snapshot = graph.get_state(config)

        print(state_snapshot)

        messages_to_show=[]
        values = getattr(state_snapshot, "values", {})
        if values and "messages" in values:
            for msg in values["messages"]:
                # LangGraph stores HumanMessage / AIMessage / ToolMessage etc.
                msg_type = msg.__class__.__name__.lower()

                # Keep only human + ai
                if msg_type in ["humanmessage", "aimessage"]:
                    if msg.content:
                        messages_to_show.append({
                            "role": "user" if msg_type == "humanmessage" else "assistant",
                            "content": msg.content.strip().split("FINAL ANSWER: ")[-1]
                        })

        return {"status" : "show message history",
                "state" : messages_to_show}
    else:
        return {"status" : "unknown command"}
    
# --for testing--

# function is async
print(f"Is function async?\nANS:{inspect.iscoroutinefunction(chat)}")


