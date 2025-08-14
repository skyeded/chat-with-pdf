import lancedb
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector

from app.utils.text_processing import text_processing
from app.utils.pdf_loader import load_pdf

from typing import List

# function for embeddings text into vectorstore with metadata
def embeddings_to_vectordb(chunks: List):

    # process chunks into appropriate format to be used when storing as class
    processed_chunks = [
        {
            "text": chunk.text,
            "metadata": {
                "filename": chunk.meta.origin.filename,
                "page_numbers": [
                    page_no
                    for page_no in sorted(
                        set(
                            prov.page_no
                            for item in chunk.meta.doc_items 
                            for prov in item.prov
                        )
                    )
                ] or None,
                "title": chunk.meta.headings[0] if chunk.meta.headings else None
            },
        }
        for chunk in chunks
    ]

    # connect to db and create function for using hf embedding model
    db = lancedb.connect("data/lancedb")
    func = get_registry().get("huggingface").create(name="intfloat/multilingual-e5-large-instruct") #hf model

    # create class for storing metadata
    class ChunkMetadata(LanceModel):
        filename: str | None
        page_numbers: List[int] | None
        title: str | None

    # create class for storing text, vector and metadata into table
    class Chunks(LanceModel):
        text: str = func.SourceField()
        vector: Vector(func.ndims()) = func.VectorField()
        metadata: ChunkMetadata

    table = db.create_table("docling", schema=Chunks, mode="overwrite")
    table.add(processed_chunks)

    return table

pdf_directory = "./data/papers" # directory of papers
documents = load_pdf(directory=pdf_directory) # load data from PDFs
chunks = text_processing(documents=documents) # process text
print(embeddings_to_vectordb(chunks=chunks).to_pandas()) # embed text into vector database