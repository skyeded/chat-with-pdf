from app.services.llm import llm
from app.utils.system_prompt import make_system_prompt
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from dotenv import load_dotenv
import lancedb



load_dotenv()

# create pdf search tool
@tool("search_vectorDB")
def search_vectorDB(query: str, num_results: int = 12) -> str:
    """
    Search the LanceDB 'docling' table for relevant context.

    IMPORTANT:
    Always pass the user's query EXACTLY as they wrote it.
    Do not paraphrase, summarize, or remove words.
    Args:
        query: The search query text.
        num_results: The number of top results to return.
    Returns:
        A string containing the top matching chunks.
    """
    db = lancedb.connect("./data/lancedb")
    table = db.open_table(name="docling")

    results_df = table.search(query).limit(num_results).to_pandas()
    contexts=[]

    for _, row in results_df.iterrows():
        filename = row["metadata"]["filename"]
        page_numbers = row["metadata"]["page_numbers"]
        title = row["metadata"]["title"]

        source_parts = []
        if filename:
            source_parts.append(filename)
            
        if page_numbers:
            source_parts.append(f"p. {', '.join(str(p) for p in page_numbers)}")
        source = f"\nSource: {' - '.join(source_parts)}"

        if title:
            source += f"\nTitle: {title}"

        contexts.append(f"{row['text']}{source}")
    
    return "\n\n".join(contexts)
    
# create pdf agent
pdf_agent = create_react_agent(model=llm,
                               tools=[search_vectorDB],
                               prompt=make_system_prompt("You task is to search for information from pdf (stored as vectorDB) and display it."
                                                         "Only go to web agent if the information could not be found from pdf files."))