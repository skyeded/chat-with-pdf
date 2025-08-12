from app.services.llm import llm
from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

model = llm
load_dotenv()

# create agent
web_agent = create_react_agent(model=model,
                               tools=[TavilySearch(max_results=3)])

input_message = {"role": "user", "content": "Hi!"}
response = web_agent.invoke({"messages": [input_message]})

for message in response["messages"]:
    message.pretty_print()
