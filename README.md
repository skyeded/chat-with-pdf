<div id="top">

<!-- HEADER STYLE: CLASSIC -->
<div align="center">

<img src="https://tk-partners.co/wp-content/uploads/2024/05/arcfusion.png" width="30%" style="position: relative; top: 0; right: 0;" alt="Project Logo"/>

# <code>Arcfusion Assignment: Chat with PDFs</code>

<em></em>

<!-- BADGES -->
<!-- local repository, no metadata badges. -->

<em>Built with the tools and technologies:</em>

<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=default&logo=FastAPI&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/LangChain-1C3C3C.svg?style=default&logo=LangChain&logoColor=white" alt="LangChain">
<img src="https://img.shields.io/badge/Docker-2496ED.svg?style=default&logo=Docker&logoColor=white" alt="Docker">
<img src="https://img.shields.io/badge/Python-3776AB.svg?style=default&logo=Python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=default&logo=Pydantic&logoColor=white" alt="Pydantic">

</div>
<br>

---

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Usage](#usage)
- [Roadmap](#roadmap)
- [Tradeoffs & Next Steps](#tradeoffs-and-next-steps)

---

## Overview

**Background**
We are exploring the capabilities of modern LLM architectures to accelerate research workflows. 
We’ve collected a set of academic papers (PDFs) on generative AI, and we need your help to 
build a backend system that enables intelligent question-answering over this corpus. 

This system should behave like a “Chat With PDF” assistant — capable of handling ambiguous 
queries, answering questions based on the documents, and performing a web search 
either when explicitly requested by the user (e.g., “Search online for...”) or when the answer 
cannot be found in the provided PDFs.

<h5> From the information given, the assignment given was to: </h5>

- Create a assistant Chatbot that answer question based on context
- The relevant context can be found inside the given PDFs (research papers)
- If the question is out-of-scope the Chatbot will extract and retrieve information from the website
- The user can also make the intent to search themselves
- The Chatbot can handle ambiguous or vague questions

<h4> Architecture (Brief) </h5>

<img src="./imgs_for_readme/rag_arch.png" alt="RAG">


<img src="./imgs_for_readme/agentic_arch.png" alt="agentic">

---

## Features

#### (v2.0 brief update summary):

➕ Change 'chat' function to **async**, use 'ainvoke' to asynchronously invoke to **avoid blocking** llm calls.

➕ Use robust **tool-calling** instead of 'string-prompt' routing, removed agent nodes and combine it into **multiagent** node.

➕ Change from **hard-coded** (fixed) thread into using **dynamic** session id, created new API endpoint to start new session.

➕ Remove internal state summary exposure, **but kept only message history and role**.

➕ Moved database connection out of tool function to **avoid** recreating indices.

➕ Tidy up project structure.

<h5> ❯ Sessions </h5>

``` Found in (./app/api/main.py) ``` 

Session are ***required*** for communicating with Chatbot.

All sessions that are created through commands are **stored** (can be viewed) until they are **deleted**.

```
active_sessions = {"default": None}
all_sessions = {} # list all sessions created

# for adding session to all sessions
def add_session(session_id: str):
    session_name = f"session_{len(all_sessions) + 1}"
    all_sessions[session_name] = session_id
```
```
@app.post("/session")
def new_session(input: SessionInput):
    if input.command == "new":
        session_id = secrets.token_urlsafe(16)
        active_sessions["default"] = session_id

        add_session(session_id)
        return {"status": "new session created...",
                "session_id": session_id}
    elif input.command == "show":
        if not all_sessions:
            return {"status" : "there are currently no active sessions, use 'new' to create a new session..."}
        
        return {"status": "list of all sessions available...",
                "sessions" : all_sessions}
    else:
        return {"status" : "unknown command"}
```

<h5> ❯ Chat </h5>

``` Found in (./app/api/main.py) ``` 

Is defined as **asynchronous** function and uses ainvoke for **non-blocking** llm calls.

```
# for communicating with chatbot
@app.post("/chat")
async def chat(input: APIInput):
    session_id = input.session_id

    if not all_sessions:
        return {"status" : "there are currently no active sessions, create a session first..."}

    if session_id:
        v_sessions = [v for v in all_sessions.values()]
        if session_id not in v_sessions:
            return {"status" : "this session id doesn't exist..."}
    else:
        return {"status": "please provide a session id..."}
    

    response = await graph.ainvoke({"messages": [ #use await for asynchronous call, changed invoke 
                                                                to ainvoke (asynchronously invoke)
        {"role" : "user",
         "content" : input.topic},
    ]},
    config={"recursion_limit" : 25, "thread_id" : session_id})
    print("Current Session ID: ", session_id)

    return {"response" : response["messages"][-1].content.split("FINAL ANSWER: ")[-1],
            "session_id" : session_id}
```

<h5> ❯ Memory </h5>

``` Found in (./app/api/main.py) ``` 

Can **clear**, **show** and **delete** memory based on session id

```
# for clearing memory or show message_history
@app.post("/memory")
async def memory(input: MInput):
    if input.command not in ['clear', 'show', 'del']:
        return {"status" : "unknown command"}
    
    session_id = input.session_id

    if not all_sessions:
            return {"status" : "there are currently no active sessions, create a session first..."}

    if session_id:
        v_sessions = [v for v in all_sessions.values()]
        if session_id not in v_sessions:
            return {"status" : "this session id doesn't exist..."}
    else:
        return {"status": "please provide a session id..."}
    
    if input.command == "clear": # clear if {"input" : "clear"}
        clear_memory_func(checkpointer, session_id)
        return {"status" : "memory cleared"}
    elif input.command == "show": # show if {"input" : "show"}
        config = {"configurable": {"thread_id": session_id}}
        state_snapshot = graph.get_state(config)

        pprint(state_snapshot.values)

        messages_to_show=[]
        values = getattr(state_snapshot, "values", {})
        if values and "messages" in values:
            for msg in values["messages"]:
                # LangGraph stores HumanMessage / AIMessage / ToolMessage etc.
                msg_type = msg.__class__.__name__.lower()

                # Keep only human + ai
                if msg_type in ["humanmessage", "aimessage"]:
                    if msg.content:
                        messages_to_show.append({
                            "role": "user" if msg_type == "humanmessage" else "assistant",
                            "content": msg.content.strip().split("FINAL ANSWER: ")[-1]
                        })

        return {"status" : "show message history",
                "session_id" : session_id,
                "state" : messages_to_show}
    elif input.command == "del":
        for k, v in all_sessions.items():
            if input.session_id == v:
                del all_sessions[k]
                break

        return {"status" : f"removed session, session id: {input.session_id}" }
    else:
        return {"status" : "unknown command"}
```

<h5> ❯ RAG Pipeline </h5>

All of these snippets can be found in ```./app/services```

**Load PDFs**
```./app/services/pdf_loader.py```
The snippets of a function below load and convert documents into text along with its metadata:
```documents``` append all the textual data (as well as **tabular data**) found from each PDF document.
```
from docling.document_converter import DocumentConverter

try:
    converter = DocumentConverter()
    document = converter.convert(source=file_path)
    documents.append(document.document)
    logging.info(f"{pdf_file} successfully loaded and extended.")

except Exception as e:
    logging.error(f"Failed to load {pdf_file}: {str(e)}")
```

**Text Processing**
```./app/services/text_processing.py```
The snippets of a function below process text from document using **HybridChunker** (tokenization-aware refinements on top of document-based hierarchical chunking) into chunks along with its metadata:
```
chunker = HybridChunker(
        tokenizer=tokenizer,
        merge_peers=True
    )

    for document in documents:
        document_fname = document.origin.filename
        logging.info(f"Separating {document_fname} into chunks")
        try:
            chunk_iter = chunker.chunk(dl_doc=document)
            chunks.extend(list(chunk_iter))
        except Exception as e:
            logging.error(f"Cannot separate {document_fname} into chunks: {str(e)}")

        logging.info(f"Separated {document_fname} into {int(len(list(chunk_iter)))} chunks")

    logging.info(f"Total number of chunks: {int(len(chunks))}")
```

**Store Memory as VectorDB**
```./app/services/ingest.py```
The snippets of a function below connect to db and create function for using hf embedding model:
```
db = lancedb.connect("data/lancedb")
func = get_registry().get("huggingface").create(name="intfloat/multilingual-e5-large-instruct") #hf model
```

The snippets of a function below create class for storing text, vector and metadata into table:
```
class Chunks(LanceModel):
    text: str = func.SourceField()
    vector: Vector(func.ndims()) = func.VectorField()
    metadata: ChunkMetadata

table = db.create_table("docling", schema=Chunks, mode="overwrite")
table.add(processed_chunks)
```
All the functions are then called to create the complete pipeline:
```
def main(pdf_directory: str):
    documents = load_pdf(directory=pdf_directory)
    chunks = text_processing(documents=documents)
    table = embeddings_to_vectordb(chunks=chunks)
    print(table.to_pandas())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDFs into LanceDB")
    parser.add_argument("--pdf-dir", type=str, required=True, help="Path to directory with PDFs")
    args = parser.parse_args()

    main(args.pdf_dir)
```

<h5> ❯ Multiagent + Tools - Search for information inside PDF(s) and on Website(s)</h5>

``` Found in (./app/agents/tools.py) ``` 

**PDF Tools:**

**search_vectorDB** tool takes a user query and searches it in the existing table of LanceDB for relevant context using **hybrid search**. It extracts texts plus metadata and formats them into readable chunks with sources. Finally, it returns all formatted contexts as a single string.

With the combination of reranker, it improves **querying performances** and **context accuracy**.

``` 
# create pdf search tool
@tool("search_vectorDB")
def search_vectorDB(query: str) -> str:
    """
    Search the LanceDB 'docling' table for relevant context.

    IMPORTANT:
    Always pass the user's query EXACTLY as they wrote it.
    Do not paraphrase, summarize, or remove words.
    Do not change the num_results.
    Args:
        query: The search query text.
        num_results: The number of top results to return.
    Returns:
        A string containing the top matching chunks.
    """
    results_df = (table.search(query, query_type="hybrid")
        .rerank(reranker=reranker)
        .limit(10)
        .to_pandas()
    )

    contexts=[]
    # get and store metadata
    for _, row in results_df.iterrows():
        filename = row["metadata"]["filename"]
        page_numbers = row["metadata"]["page_numbers"]
        title = row["metadata"]["title"]

        source_parts = []
        if filename:
            source_parts.append(filename)
            
        if page_numbers is not None and len(page_numbers) > 0:
            source_parts.append(f"p. {', '.join(str(p) for p in page_numbers)}")
        source = f"\nSource: {' - '.join(source_parts)}"

        if title:
            source += f"\nTitle: {title}"

        contexts.append(f"{row['text']}{source}")
    
    return "\n\n".join(contexts)
``` 

**Web Search Tool:**

We use DuckDuckGo Search because it’s free, requires no API key, and provides reliable general-purpose search results without usage limits. Also gemini schema is compatible with DDGS.

```
# create web search tool
search_tool = DuckDuckGoSearchRun(
    name="duckduckgo_search",
    description="Use this tool to search the web with DuckDuckGo and return the most relevant results."
``` 

**Multiagent:**

``` Found in (./app/agents/agents.py) ``` 

Multi Agent uses robust **tool-calling** by binding itself with two tools for LLM to semantically decide based on the topic of user query.

```
multiagent = create_react_agent(
    model=llm,
    tools=[search_vectorDB, search_tool],
    prompt=make_system_prompt("You are an assistant with access to two tools:\n"
        "- search_vectorDB: for searching uploaded PDFs.\n"
        "- search_web: if the answer cannot be found in PDFs.\n"
        "Always try PDFs first before using the web.\n"
        "If the user request to explicitly use web search then search the web."
))
```

**Web Agent:**

``` Found in (./app/agents/agents.py) ``` 

A separate **web agent** for **web agent node**, acts as a **fallback** incase information are not found inside PDFs.

```
web_agent = create_react_agent(
    model=llm,
    tools=[search_tool],
    prompt=make_system_prompt(
        "You  are to search for relevant context on website using the search tool."
    )
)
```

<h5> ❯ Clarification Node - Clarify ambiguous questions </h5>

``` Found in (./app/services/workflow.py) ``` 

```
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
```

<h5> ❯ Multiagent Node - Tool-calling </h5>

``` Found in (./app/services/workflow.py) ``` 
```
# node containing pdf_agent
async def multiagent_node(
    state: MessagesState,
) -> Command[Literal[END]]:
    result = await multiagent.ainvoke(state)

    ai_message = result.get("messages", [])
    user_message = state["messages"][-1].content

    prompt = f"""
        You are an assistant whose job is to check if the following content is relevant
        to the user's query. Reply only 'RELEVANT' or 'NOT RELEVANT'.

        User query: "{user_message}"
        Agent response: "{ai_message[-1].content if ai_message else ''}"
    """

    relevance = await llm.ainvoke(prompt)

    if relevance.strip().upper() != "RELEVANT":
        # LLM predicts not relevant → fallback to web
        return Command(update={"messages": state["messages"]}, goto="web_agent")

    return Command(update={"messages": result["messages"]}, goto=END)
```

```
# node containing web_agent
async def web_agent_node(
    state: MessagesState,
) -> Command[Literal[END]]:
    result = await web_agent.ainvoke(state)
    return Command(update={"messages": result["messages"]}, goto=END)
```

<h5> ❯ Lang Graph implementation </h5>
<img src="./imgs_for_readme/gen_graph.png" alt="gen">

**Description:**
This graph is created based on the efficiency and use case based on goals listed by the assignments.
The flow started by going through **clarify** node which contain an inner llm for deciding whether to continue to the next node
(multiagent_node for tool selection) based on the clarity of the question.

**multiagent** node contain **multiagent** (for PDF and Web Search) which leverage the use of RAG tool to find relevant context from PDFs and uses duckduckgo_search as a search tool for searching information relevant to the query on websites.

**web_agent** node contain **web_agent** acts as a **secondary search tool or a fallback node** incase information are not found in PDFs at the multiagent node.

---

## Project Structure

```sh
└── /
    ├── app
    │   ├── __init__.py
    │   ├── __pycache__
    │   ├── agents
    │   │   │── agents.py
    │   │   │── system_prompt.py
    │   │   │── tools.py
    │   │   │── __init__.py
    │   │   └── __pycache__
    │   ├── api
    │   │   │── main.py
    │   │   │── __init__.py
    │   │   └── __pycache__
    │   ├── models
    │   │   │── llm_model.py
    │   │   │── __init__.py
    │   │   └── __pycache__
    │   ├── services
    │   │   │── ingest.py
    │   │   │── pdf_loader.py
    │   │   │── text_processing.py
    │   │   │── workflow.py
    │   │   │── __init__.py
    │   │   └── __pycache__
    │   └── test
    │       │── __init__.py
    │       └── __pycache__
    ├── data
    │   ├── lancedb
    │   └── papers
    ├── .env
    ├── docker-compose.yml
    ├── dockerfile
    ├── .dockerignore
    ├── README.md
    ├── .gitignore
    └── requirements.txt
```

---

## Getting Started

### Prerequisites

This project requires the following dependencies:

- **Programming Language:** Python
- **Package Manager:** Pip
- **Container Runtime:** Docker
- **API for LLM:** Google API

### Installation

Build  from the source and install dependencies:

1. **Clone the repository:**

    ```sh
    ❯ git clone https://github.com/skyeded/chat-with-pdf.git
    ```

2. **Navigate to the project directory:**

    ```sh
    ❯ cd ./chat-with-pdf
    ```

3. **Install the dependencies:**


	**Using [pip](https://pypi.org/project/pip/):**

	```sh
	❯ pip install -r requirements.txt
	```

### Usage

Modify your **[.env]()**:

**Rename .env_example to .env and enter the required environmental variables:**

(langsmith is optional)
```sh
GOOGLE_API_KEY=
LANGSMITH_TRACING="true"
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
```

Run the PDFs **ingestion** script by: 

1. Input documents into ```./data/papers```
2. run bash ```python -m app.services.ingest --pdf-dir ./data/papers``` 

OR

run bash ```python -m app.services.ingest --pdf-dir <you PDFS dir>``` 

***NOTE: Please run the __PDFs ingestion__ first since I removed transactions and versions due to bloated folders***

Run the project with:

**Using [docker](https://www.docker.com/) (build image and run):**
```sh
docker-compose up --build
```

(If already built image)
```sh
docker-compose up
```

**Using [uvicorn](https://pypi.org/project/pip/):**
```sh
uvicorn app.main:app --reload
```

**Command** for API calls:-

**/session**:
-   { "**command**" : "new" } → To create new session (get session id)
-   { "**command**" : "show" } → To list or show all session (and session id)

**/chat**: 
-   { "**topic**" : "When was Microsoft found?",
      "**session_id**" : your_session_id } → To communicate with chatbot

**/memory**: 
-   { "**command**" : "clear",
      "**session_id**" : your_session_id } → To clear memory/message history for specified session
-   { "**command**" : "show",
      "**session_id**" : your_session_id } → To show message history for specified session
-   { "**command**" : "del",
      "**session_id**" : your_session_id } → To delete the specified session

*NOTE:* **To communicate with the chatbot and manipulate the memory you are required to input a session id (get session id by typing "new" command for /session as mentioned above)**

### Testing

**[Postman]():**

**To create a new session:**

<img src="./imgs_for_readme/postman_new.png" alt="post_chat">
<p></p>

**To show all sessions:**

<img src="./imgs_for_readme/postman_show.png" alt="post_chat">
<p></p>

**To communicate with the chatbot:** *(session_id required)*

<img src="./imgs_for_readme/postman_chat.png" alt="post_chat">
<p></p>

**To clear memory:**

<img src="./imgs_for_readme/postman_clear.png" alt="post_clear">
<p></p>


**To show message history:**

<img src="./imgs_for_readme/postman_mem.png" alt="post_show">
<p></p>

**To delete a session:**

<img src="./imgs_for_readme/postman_del.png" alt="post_show">
<p></p>


**[cURL](Examples):** 
**(Examples)**

**To create new sessions:**

``` sh
curl -X 'POST' \
  'http://localhost:8000/session' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "command": "new"
}'
```

**To communicate with the chatbot:**
``` sh
curl -X 'POST' \
  'http://0.0.0.0:8000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "topic": "Which prompt template gave the highest zero-shot accuracy on Spider in Zhang et al. (2024)?",
  "session_id": your_session_id
}'
```

**To clear memory:**
``` sh
curl -X 'POST' \
  'http://127.0.0.1:8000/memory' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "command": "clear",
  "session_id": your_session_id
}'
```

**You can also use the built-in docs for FASTAPI by using this url: ```http://127.0.0.1:8000/docs```** **(recommended)**

---

## Roadmap

- [X] **`Task 1`**: <strike>Create a assistant Chatbot that answer question based on context</strike>
- [X] **`Task 2`**: <strike>The relevant context can be found inside the given PDFs (research papers)</strike>
- [X] **`Task 3`**: <strike>If the question is out-of-scope the Chatbot will extract and retrieve information from the website</strike>
- [X] **`Task 4`**: <strike>The user can also make the intent to search themselves</strike>
- [X] **`Task 5`**: <strike>The Chatbot can handle ambiguous or vague questions</strike>

**Bonus Points:**
- [X] **`Task 1`**: <strike>Implement a Clarification Agent to detect vague or underspecified queries. </strike>
- [ ] **`Task 2`**: Add a basic evaluation system (e.g., golden Q&A pairs, confidence scoring).

**Real World Scenario:**
- [X] **`Example 1`**: “How many examples are enough for good accuracy” 
→ **“Enough” is vague—needs the dataset and the accuracy target**
- [X] **`Example 2`**: “Which prompt template gave the highest zero-shot accuracy on Spider in Zhang et al. 
(2024)?” → **Zhang et al. report that SimpleDDL-MD-Chat is the top zero-shot template (65–72 % EX across models)**
- [X] **`Example 3`**: What execution accuracy does davinci-codex reach on Spider with the ‘Create Table + 
Select 3’ prompt? → **Davinci-codex attains 67 % execution accuracy on the Spider dev set with that prompt style**
- [X] **`Example 4`**: “What did OpenAI release this month?” 
→ **The system should recognize this is not covered in the PDFs and search the web.**

**Revision Tasks**
- [X] **`Task 1`**: <strike>Make endpoints asynchronous and use non-blocking LLM calls.</strike>
- [X] **`Task 2`**: <strike>Remove internal state exposure from the "clear memory" endpoint and avoid hard-coded thread_id; accept a session_id. </strike>
- [X] **`Task 3`**: <strike>Replace prompt-string routing with robust tool selection (function-calling) or a classifier that decides PDF vs Web.</strike>
- [X] **`Task 4`**: <strike>Initialize DB connections/indices once at startup; avoid recreating them per request.</strike>
- [X] **`Task 5`**: <strike>Move PDF ingestion to a separate CLI/command (not at import time).</strike>
- [X] **`Task 6`**: <strike>Tidy project structure (separate api/models/services/agents) and include full source (no placeholders), plus an updated README.</strike>
---

## Tradeoffs and Next Steps

<h4> Tradeoffs </h4>

**LanceDB for vector database:**
Pros:

- Hybrid search built-in (vector + keyword via inverted indexes + reranker), good for “needle-in-a-haystack” PDFs.
- Easy local setup; Arrow/Lance columnar storage keeps things fast on disk.

Cons:

- Not as scalable or in managed clouds as Pinecone, Weaviate, or Vertex Matching Engine; fewer turnkey ops features (autoscaling, replication).
- Less community tooling.

**Gemini-2.5-Flash for LLM:**
Pros:

- Very low latency & cost for high-volume agents.
- Great for fast tools/routing steps.

Cons:

- Other models which are most costly are richer in tools usages and better context model

**Docling for document ingestion:**
Pros:

- AI-assisted PDF/Office parsing with layout.
- Great for messy enterprise PDFs.
- Works better with tables compare to traditional langchains document ingestion tools

Cons:

- More complex than traditional document ingestion tools
- Heavier dependency stack than simple text extractors

**intfloat/multilingual-e5-large-instruct as embedding model:**
Pros:

- Instruction-tuned for query-document asymmetry
- Very strong retrieval

Cons:
- 512-token limit
- Slower than smaller/base models (Heavy, not light-weighted)

**NOTE: The project also uses DuckDuckGo search instead of Tavily because it's more compatible with Gemini LLMs (schema)**

<h4> Next Steps </h4>

- Create suitable UI for easier accesibility.
- Upgrade LLMs to a more costly models for more contextual understanding, better retrieval and refined agentic behaviour (and tool calling).
- Switch to vector database that are cloud-based for scalability.
- Improve chunking (switch to Agentic chunking?)
- Find a more optimal embedding model for this use cases
- Better routing prompts
- Add text or info to which document, document pages, the information is extracted from. (Add proper metadata usage)
- Create evaluation functions

