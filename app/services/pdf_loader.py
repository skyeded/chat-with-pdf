from docling.document_converter import DocumentConverter
import logging
import os

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

documents = []
def load_pdf(directory: str):
    if not os.path.exists(directory):
        logging.error(f"Directory not found: {directory}")

    logging.info("Scanning directory: {directory}")
    for pdf_file in os.listdir(directory):
        if '/' not in directory[-1]:
            directory = str(directory)+'/'

        file_path = os.path.join(str(directory)+str(pdf_file))

        if not pdf_file.lower().endswith(".pdf"):
            logging.debug(f"Skipping non-PDF file: {pdf_file}")
            continue
        
        logging.info(f"Loading PDF: {file_path}")

        try:
            converter = DocumentConverter()
            document = converter.convert(source=file_path)
            documents.append(document.document)
            logging.info(f"{pdf_file} successfully loaded and extended.")
        except Exception as e:
            logging.error(f"Failed to load {pdf_file}: {str(e)}")
    
    logging.info(f"Total documents loaded: {len(documents)}")
    return documents