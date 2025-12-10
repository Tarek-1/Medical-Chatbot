# data_loader.py: loads a single PDF and prepares text chunks for embeddings.

from pathlib import Path
from langchain.document_loaders import PyMuPDFLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .config import DATA_PATH, INDEX_NAME, EMBEDDING_MODEL
from .retriever import get_embeddings, init_pinecone, get_vectorstore

import re


def clean_text(text: str) -> str:
    # remove soft hyphens that break words
    text = text.replace("\xad", "")

    # remove hyphenation happening across line breaks
    text = re.sub(r"-\s*\n\s*", "", text)

    # convert single newlines into spaces
    text = text.replace("\n", " ")

    # return normalized text
    return text.strip()


def filter_to_minimal_docs(docs):
    # reduce metadata and apply text cleaning per page
    minimal_docs = []
    for doc in docs:
        src = doc.metadata.get("source", "")
        page = doc.metadata.get("page", 0)
        cleaned = clean_text(doc.page_content)

        minimal_docs.append(
            Document(
                page_content=cleaned,
                metadata={"source": src, "page": page},
            )
        )
    return minimal_docs


def split_documents(docs):
    # split pages into overlapping chunks for embedding
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=550,      # target chunk size
        chunk_overlap=70     # overlap to preserve context
    )
    return splitter.split_documents(docs)


def store_embeddings(chunks):
    # initialize embedding model
    embeddings = get_embeddings(EMBEDDING_MODEL)

    # ensure Pinecone index exists
    init_pinecone()

    # load vectorstore reference
    vectorstore = get_vectorstore(
        embedding=embeddings,
        index_name=INDEX_NAME
    )

    # upload encoded document chunks to Pinecone
    vectorstore.add_documents(chunks)


def process_single_pdf(pdf_path: Path):
    # load a PDF and extract page-level documents
    loader = PyMuPDFLoader(str(pdf_path))
    docs = loader.load()

    # clean pages and strip metadata
    minimal_docs = filter_to_minimal_docs(docs)

    # convert pages into smaller semantic chunks
    chunks = split_documents(minimal_docs)

    # store chunks in Pinecone
    store_embeddings(chunks)


def prepare_data():
    # fetch all PDFs from the data directory
    print("Loading PDF files from data directory...")
    pdf_files = list(Path(DATA_PATH).glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in data directory.")
        return

    # process each PDF sequentially
    for pdf_path in pdf_files:
        print(f"Processing PDF: {pdf_path.name}")
        process_single_pdf(pdf_path)

    print("...Data preparation complete...")
