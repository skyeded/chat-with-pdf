import lancedb
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector

from app.utils.text_processing import text_processing
from app.utils.pdf_loader import load_pdf

from typing import List

pdf_directory = "./data/papers"
documents = load_pdf(directory=pdf_directory)
chunks = text_processing(documents=documents)

def embeddings_to_vectordb(chunks: List):
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

    db = lancedb.connect("data/lancedb")
    func = get_registry().get("huggingface").create(name="BAAI/bge-m3")

    class ChunkMetadata(LanceModel):
        filename: str | None
        page_numbers: List[int] | None
        title: str | None

    class Chunks(LanceModel):
        text: str = func.SourceField()
        vector: Vector(func.ndims()) = func.VectorField()
        metadata: ChunkMetadata

    table = db.create_table("docling", schema=Chunks, mode="overwrite")
    table.add(processed_chunks)

    return table

print(embeddings_to_vectordb(chunks=chunks).to_pandas())