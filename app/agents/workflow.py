from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import MessagesState, END, StateGraph, START
from langgraph.types import Command
from app.agents.pdf_agent import pdf_agent
from app.agents.web_agent import web_agent
from dotenv import load_dotenv

from typing import Literal

load_dotenv()

def get_next_node(last_message: BaseMessage, goto: str):
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return END
    return goto

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

def web_node(
    state: MessagesState,
) -> Command[Literal["search_pdf", END]]:
    result = web_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "search_pdf")
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

workflow = StateGraph(MessagesState)
workflow.add_node("search_pdf", pdf_node)
workflow.add_node("search_web", web_node)

workflow.add_edge(START, "search_pdf")
graph = workflow.compile()