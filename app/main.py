from fastapi import FastAPI
from pydantic import BaseModel, Field
import inspect
from app.agents.workflow import graph, clear_memory_func, checkpointer
from pprint import pprint
import secrets

app = FastAPI()
active_sessions = {"default": None}

# initialize endpoint
@app.get("/")
def read_root():
    return {"Hello" : "World"}

# class for communicating with chatbot
class APIInput(BaseModel):
    topic: str = Field(description="Input topic for Chatbot.")
    session_id: str | None = Field(default=None, description="Optional session ID for multi-session support.")

# class for clearing memory or show message_history
class CMInput(BaseModel):
    clear_memory: str = Field(description="For clearing memory from a single session.")
    session_id: str | None = Field(default=None, description="Optional session ID for multi-session support.")

@app.post("/new_session")
def new_session():
    session_id = secrets.token_urlsafe(16)
    return {"status": "new session created", "session_id": session_id}

# for communicating with chatbot
@app.post("/chat")
async def chat(input: APIInput):
    session_id = input.session_id

    if not session_id:
        print("Session ID not found!\nCreating new session id...")
        session_id = secrets.token_urlsafe(16)

    response = await graph.ainvoke({"messages": [ #use await for asynchronous call, changed invoke to ainvoke (asynchronously invoke)
        {"role" : "user",
         "content" : input.topic},
    ]},
    config={"recursion_limit" : 25, "thread_id" : session_id})
    print("Current Session ID: ", session_id)

    return {"response" : response["messages"][-1].content.split("FINAL ANSWER: ")[-1],
            "session_id" : session_id}

# for clearing memory or show message_history
@app.post("/clear_memory")
async def clear_memory(input: CMInput):
    session_id = input.session_id

    if not session_id:
        return {"status": "Please input session id..."}
    
    if input.clear_memory == "clear": # clear if {"input" : "clear"}
        clear_memory_func(checkpointer, session_id)
        return {"status" : "memory cleared"}
    elif input.clear_memory == "show": # show if {"input" : "show"}
        config = {"configurable": {"thread_id": session_id}}
        state_snapshot = graph.get_state(config)

        pprint(state_snapshot.values)

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
                "session_id" : session_id,
                "state" : messages_to_show}
    else:
        return {"status" : "unknown command"}
    
# --for testing--

# function is async
print(f"Is function async?\nANS:{inspect.iscoroutinefunction(chat)}")


