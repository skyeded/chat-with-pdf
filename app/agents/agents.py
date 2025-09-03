from app.models.llm_model import llm
from langgraph.prebuilt import create_react_agent
from app.agents.tools import search_vectorDB, search_tool
from app.agents.system_prompt import make_system_prompt
from dotenv import load_dotenv

load_dotenv()

multiagent = create_react_agent(
    model=llm,
    tools=[search_vectorDB, search_tool],
    prompt=make_system_prompt("You are an assistant with access to two tools:\n"
        "- search_vectorDB: for searching uploaded PDFs.\n"
        "- search_web: if the answer cannot be found in PDFs.\n"
        "Always try PDFs first before using the web.\n"
        "If the user request to explicitly use web search then search the web."
))

web_agent = create_react_agent(
    model=llm,
    tools=[search_tool],
    prompt=make_system_prompt(
        "You  are to search for relevant context on website using the search tool."
    )
)