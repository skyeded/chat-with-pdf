from app.utils.pdf_loader import load_pdf
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

import logging

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

TOKENIZER_MODEL="BAAI/bge-m3"
MAX_TOKENS=8192

pdf_directory = "./data/papers"
documents = load_pdf(directory=pdf_directory)

def save_as_text(chunk: str):
    with open('../example_data/chunks', 'w', encoding='utf-8') as f:
        f.write(chunk)

chunks = list()
def text_processing(documents: list):
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained(TOKENIZER_MODEL),
        max_tokens=MAX_TOKENS,
    )

    chunker = HybridChunker(
        tokenizer=tokenizer,
        merge_peers=True
    )

    for document in documents:
        document_fname = document.origin.filename
        logging.info(f"Separating {document_fname} into chunks")
        try:
            chunk_iter = chunker.chunk(dl_doc=document)
            chunks.extend(chunk_iter)
        except Exception as e:
            logging.error(f"Cannot separate {document_fname} into chunks: {str(e)}")

    for chunk in chunks[:10]:
        save_as_text(chunk.text)

    return chunks

print(text_processing(documents=documents))