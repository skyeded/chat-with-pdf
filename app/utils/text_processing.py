from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

import logging

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

TOKENIZER_MODEL="intfloat/multilingual-e5-large-instruct"
MAX_TOKENS=512

def save_as_text(chunk: str):
    with open('./app/example_data/chunks', 'w', encoding='utf-8') as f:
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
            chunks.extend(list(chunk_iter))
        except Exception as e:
            logging.error(f"Cannot separate {document_fname} into chunks: {str(e)}")

        logging.info(f"Separated {document_fname} into {int(len(list(chunk_iter)))} chunks")

    logging.info(f"Total number of chunks: {int(len(chunks))}")
    # for chunk in chunks[:10]:
    #     save_as_text(chunk.text)

    return chunks