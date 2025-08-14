from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import MessagesState, END, StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.message import RemoveMessage, REMOVE_ALL_MESSAGES
from langgraph.types import Command
from app.agents.pdf_agent import pdf_agent
from app.agents.web_agent import web_agent
from app.agents.clarification_agent import clarification_agent
from dotenv import load_dotenv

from typing import Literal

load_dotenv()

# create short-term memory (for one session)
checkpointer = InMemorySaver()

# function for deciding whether to END or route to the next node
def get_next_node(last_message: BaseMessage, goto: str):
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return END
    return goto

# node containing clarification_agent
def clarification_node(
    state: MessagesState,
) -> Command[Literal["search_pdf", "search_web", END]]:
    result = clarification_agent.invoke(state)
    if "pdf_agent" in result["messages"][-1].content:
        goto = get_next_node(result["messages"][-1], "search_pdf")
    elif "web_agent" in result["messages"][-1].content:
        goto = get_next_node(result["messages"][-1], "search_web")
    else:
        goto = END
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="clarify"
    )
    return Command(
        update={
            # share internal message history of research agent with other agents
            "messages": result["messages"],
        },
        goto=goto,
    )

# node containing pdf_agent
def pdf_node(
    state: MessagesState,
) -> Command[Literal["search_web", END]]:
    result = pdf_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "search_web")
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="search_pdf"
    )
    return Command(
        update={
            # share internal message history of research agent with other agents
            "messages": result["messages"],
        },
        goto=goto,
    )

# node containing web_agent
def web_node(
    state: MessagesState,
) -> Command[Literal[END]]:
    result = web_agent.invoke(state)
    goto = END
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="search_web"
    )
    return Command(
        update={
            # share internal message history of research agent with other agents
            "messages": result["messages"],
        },
        goto=goto,
    )

# function for clearning the memory
def clear_memory_func(memory: BaseCheckpointSaver, thread_id: str) -> None:
    """ Clear the memory for a given thread_id. """
    try:
        # If it's an InMemorySaver (which MemorySaver is an alias for),
        # we can directly clear the storage and writes
        if hasattr(memory, 'storage') and hasattr(memory, 'writes'):
            # Clear all checkpoints for this thread_id (all namespaces)
            memory.storage.pop(thread_id, None)

            # Clear all writes for this thread_id (for all namespaces)
            keys_to_remove = [key for key in memory.writes.keys() if key[0] == thread_id]
            for key in keys_to_remove:
                memory.writes.pop(key, None)

            print(f"Memory cleared for thread_id: {thread_id}")
            return

    except Exception as e:
        print(f"Error clearing InMemorySaver storage for thread_id {thread_id}: {e}")

# create graph
workflow = StateGraph(MessagesState)
workflow.add_node("clarify", clarification_node)
workflow.add_node("search_pdf", pdf_node)
workflow.add_node("search_web", web_node)

workflow.add_edge(START, "clarify")
graph = workflow.compile(checkpointer=checkpointer) # add short_term memory to graph