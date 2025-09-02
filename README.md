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
- [Acknowledgments](#acknowledgments)

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

<h5> ❯ RAG Pipeline + PDF Agent - Search for information inside PDFs</h5>

``` Found in (./app/agents/pdf_agent.py) ``` 

``` 
@tool("search_vectorDB")
def search_vectorDB(query: str) -> str:
.....
	return "\n\n".join(contexts)
``` 

<h5> ❯ Web Search Tool + Web Agent - Search for informaton on website</h5>

``` Found in (./app/agents/web_agent.py) ``` 

```search_tool = DuckDuckGoSearchRun()``` 

``` 
web_agent = 
	create_react_agent(model=llm,
	tools=[search_tool],
	prompt=make_system_prompt(
		"Your task is to search for information and display information found on website."
		)
	)
```

<h5> ❯ Clarification Agent - Clarify ambiguous questions </h5>

``` Found in (./app/agents/clarification_agent.py) ``` 

```
clarification_agent = create_react_agent(model=llm,
	tools=[],
	prompt="Your task is to detect questions that are ambiguous or vague."
		"For example: if the user asked 'How many examples are enough for good accuracy?' is vague."
		"\n\nUse pdf_agent first to search for information inside the pdf, respond 'pdf_agent'."
		"If information are not found inside the pdf, use web_agent to search 
		information on website instead, respond 'web_agent'."
		"\n\nIf the question is too vague then ask them in a short sentence to provide more 
		information or 'clarity' and prefix your response with FINAL ANSWER: ")
```

<h5> ❯ Lang Graph implementation </h5>
<img src="./imgs_for_readme/gen_graph.png" alt="gen">

**Description:**
This graph is created based on the efficiency and use case based on goals listed by the assignments.
The flow started by going through **clarify** node which contain **clarification_agent** for deciding whether to continue to the next node
based on the clarity of the question.

**search_pdf** node contain **pdf_agent** which leverage the use of RAG tool to find relevant context from PDFs.
**search_web** node contain **web_agent** which uses duckduckgo_search as a search tool for searching information relevant to the query on websites.

If the **clarify** node detects that the question is out-of-scope or results are not found from searching inside PDFs it moves to **search_web** node for context.

The function below is the core function to decide whether to move to the next node or END the traversal (and return the response):
```
def get_next_node(last_message: BaseMessage, goto: str):
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return END
    return goto
```
``` This function and functions for creating nodes can be found in (./app/agents/workflow.py) ``` 

<h5> ❯ RAG Pipeline </h5>

All of these snippets can be found in ```./app/utils```

**Load PDFs**
The snippets of a function below load and convert documents into text along with its metadata:
```documents``` append all the textual data found from each PDF document.
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
The snippets of a function below process text from document using HybridChunker 
into chunks along with its metadata:
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
pdf_directory = "./data/papers" # directory of papers
documents = load_pdf(directory=pdf_directory) # load data from PDFs
chunks = text_processing(documents=documents) # process text
print(embeddings_to_vectordb(chunks=chunks).to_pandas()) # embed text into vector database
```

---

## Project Structure

```sh
└── /
    ├── app
    │   ├── __init__.py
    │   ├── __pycache__
    │   ├── agents
    │   ├── main.py
    │   ├── services
    │   ├── test
    │   └── utils
    ├── data
    │   ├── lancedb
    │   └── papers
    ├── docker-compose.yml
    ├── dockerfile
    ├── README.md
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

Run the PDFs ingestion script by:

1. Input documents into ```./data/papers```
2. run bash ```python -m ./app/utils/memory_store```

### Testing

**[Postman]():**

**To communicate with the chatbot:**

<img src="./imgs_for_readme/postman_chat.png" alt="post_chat">
<p></p>

**To clear memory:**

<img src="./imgs_for_readme/postman_clear.png" alt="post_clear">
<p></p>


**To show message history:**

<img src="./imgs_for_readme/postman_mem.png" alt="post_show">
<p></p>

**[cURL]():**

**To communicate with the chatbot:**
``` sh
curl -X 'POST' \
  'http://0.0.0.0:8000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "topic": "Which prompt template gave the highest zero-shot accuracy on Spider in Zhang et al. (2024)?"
}'
```

**To clear memory:**
``` sh
curl -X 'POST' \
  'http://127.0.0.1:8000/clear_memory' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "clear_memory": "clear"
}'
```

**To show messages history:**
``` sh
curl -X 'POST' \
  'http://127.0.0.1:8000/clear_memory' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "clear_memory": "show"
}'
```

**You can also use the built-in docs for FASTAPI by using this url: ```http://127.0.0.1:8000/docs```**

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
- [ ] **`Task 5`**: Move PDF ingestion to a separate CLI/command (not at import time).
- [ ] **`Task 6`**: Tidy project structure (separate api/models/services/agents) and include full source (no placeholders), plus an updated README.
---

## Tradeoffs and Next Steps

<h4> _Tradeoffs_ </h4>

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

<h4> _Next Steps_ </h4>

- Create suitable UI for easier accesibility.
- Upgrade LLMs to a more costly models for more contextual understanding, better retrieval and refined agentic behaviour (and tool calling).
- Switch to vector database that are cloud-based for scalability.
- Improve chunking (switch to Agentic chunking?)
- Find a more optimal embedding model for this use cases
- Better routing prompts
- Add text or info to which document, document pages, the information is extracted from. (Add proper metadata usage)
- Create evaluation functions

