from app.services.llm import llm
from web_agent import web_agent
from langgraph_supervisor import create_supervisor

model = llm

supervisor = create_supervisor(
    model = model,
    agents = [web_agent],
    prompt = (
        """
            You are a supervisor managing two agents.
        """
    )
)