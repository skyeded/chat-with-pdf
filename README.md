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
    - [Project Index](#project-index)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Testing](#testing)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Overview

Background 
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


<img src="./imgs_for_readme/agentic_arch.png" alt="RAG">
---

## Features

<h5> ❯ RAG Pipeline + PDF Agent - Search for information inside PDFs</h5>

<code>@tool("search_vectorDB")
def search_vectorDB(query: str) -> str:
.....
return "\n\n".join(contexts)</code>

<h5> ❯ Web Search Tool + Web Agent - Search for informaton on website</h5>
<code>search_tool = DuckDuckGoSearchRun() </code>

<code>web_agent = 
create_react_agent(model=llm,
tools=[search_tool],
prompt=make_system_prompt(
	"Your task is to search for information and display information found on website."
	)
)</code>

<h5> ❯ Clarification Agent - Clarify ambiguous questions </h5>
<code>clarification_agent = create_react_agent(model=llm,
tools=[],
prompt="Your task is to detect questions that are ambiguous or vague."
       "For example: if the user asked 'How many examples are enough for good accuracy?' is vague."
       "\n\nUse pdf_agent first to search for information inside the pdf, respond 'pdf_agent'."
       "If information are not found inside the pdf, use web_agent to search information on website instead, respond 'web_agent'."
       "\n\nIf the question is too vague then ask them in a short sentence to provide more information or 'clarity' and prefix your response with FINAL ANSWER: ")</code>

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

### Installation

Build  from the source and intsall dependencies:

1. **Clone the repository:**

    ```sh
    ❯ git clone ../
    ```

2. **Navigate to the project directory:**

    ```sh
    ❯ cd 
    ```

3. **Install the dependencies:**

<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![pip][pip-shield]][pip-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [pip-shield]: https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white -->
	<!-- [pip-link]: https://pypi.org/project/pip/ -->

	**Using [pip](https://pypi.org/project/pip/):**

	```sh
	❯ pip install -r requirements.txt
	```

### Usage

Run the project with:

**Using [docker](https://www.docker.com/):**
```sh
docker-compose up --build
```
**Using [uvicorn](https://pypi.org/project/pip/):**
```sh
uvicorn app.main:app --reload
```

---

## Roadmap

- [X] **`Task 1`**: <strike>Implement feature one.</strike>
- [ ] **`Task 2`**: Implement feature two.
- [ ] **`Task 3`**: Implement feature three.

---

## Acknowledgments

- Credit `contributors`, `inspiration`, `references`, etc.

<div align="right">

[![][back-to-top]](#top)

</div>


[back-to-top]: https://img.shields.io/badge/-BACK_TO_TOP-151515?style=flat-square


---
