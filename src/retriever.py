# retriever.py: sets up embeddings, Pinecone index access, and the retriever used for RAG search.

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Pinecone as LC_Pinecone
from pinecone import Pinecone, ServerlessSpec
from .config import PINECONE_API_KEY, INDEX_NAME, EMBEDDING_MODEL


# Returns a HuggingFace embedding model used for encoding text.
def get_embeddings(model_name=EMBEDDING_MODEL):
    return HuggingFaceEmbeddings(model_name=model_name)


# Ensures the Pinecone index exists and returns a reference to it.
def init_pinecone(
    api_key=PINECONE_API_KEY,
    index_name=INDEX_NAME,
    dimension=1024,
    metric="cosine",
    cloud="aws",
    region="eu-west-1",
):
    pc = Pinecone(api_key=api_key)
    existing_indexes = [index["name"] for index in pc.list_indexes()]

    # Create the index on first startup if missing
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud=cloud, region=region),
        )

    return pc.Index(index_name)


# Loads an existing Pinecone index and wraps it as a LangChain vectorstore.
def get_vectorstore(embedding=None, index_name=INDEX_NAME, model_name=EMBEDDING_MODEL):
    if embedding is None:
        embedding = get_embeddings(model_name)
    return LC_Pinecone.from_existing_index(embedding=embedding, index_name=index_name)


# Creates a retriever used for semantic search during RAG.
# Applies a similarity threshold to filter weak matches.
def get_retriever(index_name=INDEX_NAME, model_name=EMBEDDING_MODEL, k=8, score_threshold=0.10):
    """
    Returns a Pinecone-backed retriever:
    - encodes the query using the embedding model
    - retrieves the top-k most similar chunks
    - filters results using a similarity score threshold
    """

    vectorstore = get_vectorstore(model_name=model_name, index_name=index_name)

    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": k,
            "score_threshold": score_threshold,
        },
    )
    return retriever
