from langchain.chat_models import init_chat_model

llm = init_chat_model(
    model = "llama3.1:8b",
    temperature = 0,
    model_provider = "ollama"
)

# messages = [
#     ("system",
#      "You are a helpful assistant."),
#      ("human", "Where can I buy an ice cream?")
# ]

# response = llm.invoke(messages)
# print(response.content)