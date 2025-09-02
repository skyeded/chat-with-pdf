from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState, END, StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from app.models.llm_model import llm
from app.agents.multiagent import multiagent
from dotenv import load_dotenv

from typing import Literal

load_dotenv()

# create short-term memory (for one session)
checkpointer = InMemorySaver()

# node containing clarification_agent
async def clarification_node(
    state: MessagesState,
) -> Command[Literal[END]]:
    message = state["messages"][-1].content

    prompt = f"""
            You are an assistant whose job is to check if a user question is ambiguous.
            If it is ambiguous, rewrite it as a clarification question.
            If it is clear, reply only with 'CLEAR'.

            For example, 'How many examples are enough for good accuracy?' → 
            Depends on dataset complexity and target accuracy.
            Please clarify the dataset size, type, and your accuracy goal.

            User question: "{message}"
            """
    llm_response = await llm.apredict(prompt)

    if llm_response.strip().upper() != "CLEAR":
        clarification_msg = HumanMessage(content=llm_response.strip(), name="clarification")
        return Command(
            update={"messages": state["messages"] + [clarification_msg]},
            goto=END
        )

    # Query is clear → pass messages to next node
    return Command(update={"messages": state["messages"]}, goto="multiagent")

# node containing pdf_agent
async def multiagent_node(
    state: MessagesState,
) -> Command[Literal[END]]:
    result = await multiagent.ainvoke(state)
    print(result)
    return Command(update={"messages": result["messages"]}, goto=END)

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
workflow.add_node("multiagent", multiagent_node)

workflow.add_edge(START, "clarify")
graph = workflow.compile(checkpointer=checkpointer) # add short_term memory to graph