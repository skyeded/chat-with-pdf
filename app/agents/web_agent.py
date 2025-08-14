from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import create_react_agent
from app.utils.system_prompt import make_system_prompt
from app.services.llm import llm
from dotenv import load_dotenv

load_dotenv()

# DuckDuckGo is more compatible with gemini model
search_tool = DuckDuckGoSearchRun()

# create web agent
web_agent = create_react_agent(
    model=llm,
    tools=[search_tool],
    prompt=make_system_prompt(
        "Your task is to search for information and display information found on website."
    )
)