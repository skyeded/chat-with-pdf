from app.services.llm import llm
from app.utils.system_prompt import make_system_prompt
from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

# create web agent
web_agent = create_react_agent(model=llm,
                               tools=[TavilySearch(max_results=3)],
                               prompt=make_system_prompt("Your task is to search for information and display information found on website."))
