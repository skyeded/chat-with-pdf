from langchain.tools import tool
from lancedb.rerankers import LinearCombinationReranker
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv
import lancedb

load_dotenv()

# connect to vectordb
db = lancedb.connect("./data/lancedb")
table = db.open_table(name="docling")

# implement reranker
table.create_fts_index("text", replace=True)
reranker = LinearCombinationReranker()

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
    results_df = ( table.search(query, query_type="hybrid")
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

search_tool = DuckDuckGoSearchRun()