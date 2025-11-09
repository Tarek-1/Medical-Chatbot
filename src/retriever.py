# retriever.py: handles embeddings and Pinecone-based document retrieval.

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import Pinecone as LC_Pinecone

from pinecone import Pinecone, ServerlessSpec

from .config import PINECONE_API_KEY, INDEX_NAME, EMBEDDING_MODEL


# Initializes HuggingFace embeddings.
def get_embeddings(model_name=EMBEDDING_MODEL):
    return HuggingFaceEmbeddings(model_name=model_name)


# Connects to Pinecone and creates an index if it doesn't exist.
def init_pinecone(
    api_key=PINECONE_API_KEY,
    index_name=INDEX_NAME,
    dimension=384,
    metric="cosine",
    cloud="aws",
    region="us-east-1",
):
    pc = Pinecone(api_key=api_key)
    existing_indexes = [index["name"] for index in pc.list_indexes()]

    # Create index only if it doesn't exist already
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud=cloud, region=region),
        )

    return pc.Index(index_name)


# Loads an existing Pinecone index and returns a vector store.
def get_vectorstore(embedding=None, index_name=INDEX_NAME, model_name=EMBEDDING_MODEL):
    if embedding is None:
        embedding = get_embeddings(model_name)
    return LC_Pinecone.from_existing_index(embedding=embedding, index_name=index_name)


# Builds and returns a retriever for document search with score filtering.
def get_retriever(index_name=INDEX_NAME, model_name=EMBEDDING_MODEL, k=3, score_threshold=0.75):
    """
    Creates a retriever that fetches document chunks from Pinecone,
    but filters out results below the given similarity score threshold.

    Parameters:
        index_name (str): Name of the Pinecone index.
        model_name (str): Embedding model to use for search.
        k (int): Number of top chunks to retrieve.
        score_threshold (float): Minimum similarity score required (0–1 range).
    """

    # Loads the existing vectorstore (from Pinecone) using embeddings.
    vectorstore = get_vectorstore(model_name=model_name, index_name=index_name)

    # Creates a retriever that only returns documents with similarity scores above the threshold.
    # 'similarity_score_threshold' ensures irrelevant results are filtered automatically.
    return vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": k,
            "score_threshold": score_threshold,  # Only returns docs with high similarity scores (e.g., ≥ 0.75)
        },
    )
