from langgraph.prebuilt import create_react_agent
from app.services.llm import llm

clarification_agent = create_react_agent(model=llm,
                                         tools=[],
                                         prompt="Your task is to detect questions that are ambiguous or vague."
                                                "For example: if the user asked 'How many examples are enough for good accuracy?' is vague."
                                                "\n\nUse pdf_agent first to search for information inside the pdf, respond 'pdf_agent'."
                                                "If information are not found inside the pdf, use web_agent to search information on website instead, respond 'web_agent'."
                                                "\n\nIf the question is too vague then ask them in a short sentence to provide more information or 'clarity' and prefix your response with FINAL ANSWER: ")