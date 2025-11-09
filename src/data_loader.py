# data_loader.py — loads PDF documents and prepares text chunks for embeddings.

from langchain.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# from config.py → constants and paths
from .config import DATA_PATH, INDEX_NAME, EMBEDDING_MODEL

# from retriever.py → embedding model + Pinecone index setup
from .retriever import get_embeddings, init_pinecone, get_vectorstore


# Loads all PDF files from the data directory defined in config.py.
def load_pdf_files(data_dir=DATA_PATH):
    loader = DirectoryLoader(data_dir, glob="*.pdf", loader_cls=PyPDFLoader)
    return loader.load()


# Cleans metadata and keeps only the essential fields: source and page.
def filter_to_minimal_docs(docs):
    minimal_docs = []
    for doc in docs:
        src = doc.metadata["source"]
        page = doc.metadata["page"]
        minimal_docs.append(
            Document(
                page_content=doc.page_content,
                metadata={"source": src, "page": page},
            )
        )
    return minimal_docs


# Splits documents into overlapping text chunks for embedding and retrieval.
def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=20
    )
    return splitter.split_documents(docs)


# Creates embeddings and uploads document chunks into Pinecone.
def store_embeddings(chunks):
    embeddings = get_embeddings(EMBEDDING_MODEL)     # ← from retriever.py
    init_pinecone()                                  # ← from retriever.py
    vectorstore = get_vectorstore(embedding=embeddings, index_name=INDEX_NAME)  # ← from retriever.py
    vectorstore.add_documents(chunks)
    return vectorstore


# Main pipeline to prepare and upload data.
def prepare_data():
    print("Loading PDF files...")
    documents = load_pdf_files()

    print("Cleaning metadata...")
    minimal_docs = filter_to_minimal_docs(documents)

    print("Splitting into chunks...")
    chunks = split_documents(minimal_docs)

    print("Uploading embeddings to Pinecone...")
    store_embeddings(chunks)

    print("...Data preparation complete...")
