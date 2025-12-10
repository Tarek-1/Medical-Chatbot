# source_manager.py: stores and retrieves sources linked to medical answers.

from typing import List, Dict, Any
from collections import defaultdict
import uuid
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain_huggingface import HuggingFaceEmbeddings
from .config import EMBEDDING_MODEL


class SourceManager:
    """
    Stores per-answer source information in memory and supports
    later lookup when the user asks for sources.
    """

    def __init__(self):
        # Embedding model for semantic comparison between queries and past answers.
        self.embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        # In-memory list of stored QA entries.
        self.history: List[Dict[str, Any]] = []

    def add_entry(self, question: str, answer: str, sources: List[Dict[str, Any]]):
        """
        Store a question/answer pair and its sources.
        """
        if not sources:
            return

        entry_id = str(uuid.uuid4())
        text_for_embedding = f"{question}\n{answer}"

        embedding = self.embedding_model.embed_query(text_for_embedding)

        self.history.append(
            {
                "id": entry_id,
                "question": question,
                "answer": answer,
                "sources": sources,
                "embedding": embedding,
            }
        )

    def extract_sources_from_docs(self, retrieved_docs: List[Any]) -> List[Dict[str, Any]]:
        """
        Build a compact list of sources from retrieved documents.
        """
        pages_by_book = defaultdict(list)

        # Collect page numbers by book/source.
        for doc in retrieved_docs:
            md = getattr(doc, "metadata", None) or {}
            book = md.get("source", "Unknown source")
            try:
                page = int(md.get("page"))
            except Exception:
                # Skip docs without a valid integer page.
                continue
            pages_by_book[book].append(page)

        sources: List[Dict[str, Any]] = []

        # For each book, sort pages, merge consecutive ranges, and format.
        for book, pages in pages_by_book.items():
            pages = sorted(set(pages))
            if not pages:
                continue

            ranges: List[str] = []
            start = last_page = pages[0]

            for p in pages[1:]:
                if p == last_page + 1:
                    # Extend current range.
                    last_page = p
                else:
                    # Close current range.
                    if start == last_page:
                        ranges.append(f"{start}")
                    else:
                        ranges.append(f"{start} to {last_page}")
                    start = last_page = p

            # Close the final range.
            if start == last_page:
                ranges.append(f"{start}")
            else:
                ranges.append(f"{start} to {last_page}")

            # One source entry per range.
            for r in ranges:
                sources.append({"source": book, "page": r})

        return sources

    def add_entry_from_docs(
        self,
        question: str,
        answer: str,
        retrieved_docs: List[Any],
    ) -> List[Dict[str, Any]]:
        """
        Convenience helper:
        - extract sources from retrieved_docs,
        - store them with the QA entry,
        - return the sources.
        """
        sources = self.extract_sources_from_docs(retrieved_docs)
        if sources:
            self.add_entry(question, answer, sources)
        return sources

    def get_sources_for_query(self, user_query: str) -> List[Dict[str, Any]]:
        """
        Return the most relevant stored sources for a user query.
        """
        if not self.history:
            return []

        lower = user_query.lower().strip()

        # Short generic source questions → return latest entry's sources.
        generic_keywords = [
            "source",
            "sources",
            "reference",
            "references",
            "cite",
            "citation",
            "what page",
            "which page",
        ]
        if any(k in lower for k in generic_keywords) and len(lower.split()) <= 6:
            return self.history[-1]["sources"]

        # For more detailed queries, use semantic similarity.
        request_embedding = self.embedding_model.embed_query(user_query)
        request_vec = np.array(request_embedding).reshape(1, -1)

        all_embeddings = np.array([entry["embedding"] for entry in self.history])
        similarities = cosine_similarity(request_vec, all_embeddings)[0]

        best_idx = int(np.argmax(similarities))
        best_score = similarities[best_idx]

        if best_score < 0.30:
            return []

        return self.history[best_idx]["sources"]
