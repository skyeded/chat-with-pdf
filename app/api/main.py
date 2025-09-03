from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.services.workflow import graph, clear_memory_func, checkpointer
from pprint import pprint
import inspect
import secrets
import redis

app = FastAPI()
# active_sessions = {"default": None}
# all_sessions = {} # list all sessions created

# use redis for shared session ID between all workers
def get_redis_client():
    # Try localhost first
    for host in ["localhost", "redis"]:
        try:
            client = redis.Redis(host=host, port=6379, db=0, decode_responses=True)
            client.ping()
            print(f"Successfully connected to Redis at {host}:6379.")
            return client
        except redis.exceptions.ConnectionError:
            print(f"Could not connect to Redis at {host}:6379, trying next...")
    # If both fail
    raise ConnectionError("Could not connect to Redis at localhost or redis.")

# Usage
redis_client = get_redis_client()

SESSION_ID = "session_id"

# for adding session to all sessions (DEPRECATED)
# def add_session(session_id: str):
#     session_name = f"session_{len(all_sessions) + 1}"
#     all_sessions[session_name] = session_id

# initialize endpoint
@app.get("/")
def read_root():
    return {"Hello" : "World"}

class SessionInput(BaseModel):
    command: str = Field(description="Enter command for creating new session or view all sessions.")

# class for communicating with chatbot
class APIInput(BaseModel):
    topic: str = Field(description="Input topic for Chatbot.")
    session_id: str | None = Field(default=None, description="Optional session ID for multi-session support.")

# class for clearing memory or show message_history
class MInput(BaseModel):
    command: str = Field(description="Enter command for clear_memory or show messages history.")
    session_id: str | None = Field(default=None, description="Optional session ID for multi-session support.")

@app.post("/session")
def new_session(input: SessionInput):
    if input.command == "new":
        session_id = secrets.token_urlsafe(16)

        # add_session(session_id)
        redis_client.sadd(SESSION_ID, session_id)
        return {"status": "new session created...",
                "session_id": session_id}
    elif input.command == "show":
        # get all sessions
        all_sessions = list(redis_client.smembers(SESSION_ID))

        sessions_dict = {
            f"session_{i+1}": session_id 
            for i, session_id in enumerate(all_sessions)
        }

        if not all_sessions:
            return {"status" : "there are currently no active sessions, use 'new' to create a new session..."}
        
        return {"status": "list of all sessions available...",
                "sessions" : sessions_dict}
    else:
        return {"status" : "unknown command"}


# for communicating with chatbot
@app.post("/chat")
async def chat(input: APIInput):
    session_id = input.session_id

    all_sessions = list(redis_client.smembers(SESSION_ID))

    if not all_sessions:
        return {"status" : "there are currently no active sessions, create a session first..."}

    if session_id:
        v_sessions = [v for v in all_sessions]
        if session_id not in v_sessions:
            return {"status" : "this session id doesn't exist..."}
    else:
        return {"status": "please provide a session id..."}
    

    response = await graph.ainvoke({"messages": [ #use await for asynchronous call, changed invoke to ainvoke (asynchronously invoke)
        {"role" : "user",
         "content" : input.topic},
    ]},
    config={"recursion_limit" : 25, "thread_id" : session_id})
    print("Current Session ID: ", session_id)

    return {"response" : response["messages"][-1].content.split("FINAL ANSWER: ")[-1],
            "session_id" : session_id}

# for clearing memory or show message_history
@app.post("/memory")
async def memory(input: MInput):
    if input.command not in ['clear', 'show', 'del']:
        return {"status" : "unknown command"}
    
    all_sessions = list(redis_client.smembers(SESSION_ID))
    
    session_id = input.session_id

    if not all_sessions:
            return {"status" : "there are currently no active sessions, create a session first..."}

    if session_id:
        v_sessions = [v for v in all_sessions]
        if session_id not in v_sessions:
            return {"status" : "this session id doesn't exist..."}
    else:
        return {"status": "please provide a session id..."}
    
    if input.command == "clear": # clear if {"input" : "clear"}
        clear_memory_func(checkpointer, session_id)
        return {"status" : "memory cleared"}
    elif input.command == "show": # show if {"input" : "show"}
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
    elif input.command == "del":
        redis_client.srem(SESSION_ID, session_id)
        return {"status" : f"removed session, session id: {input.session_id}" }
    else:
        return {"status" : "unknown command"}
    
# --for testing--

# function is async
print(f"Is function async?\nANS:{inspect.iscoroutinefunction(chat)}")


