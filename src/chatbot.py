# chatbot.py: handles message classification, document retrieval,
# medical answering, saving sources, and updating conversation memory.

from langchain.chains.combine_documents import create_stuff_documents_chain

from .summary_memory import SummaryMemory
from .llm_interface import get_main_llm, get_classifier_llm
from .retriever import get_retriever
from .prompts import get_medical_prompt, get_classifier_prompt
from .source_manager import SourceManager


# Initialize conversation summary used for context.
summary_memory = SummaryMemory()

# Initialize manager for per-answer sources.
source_manager = SourceManager()


def answer_question(question: str):
    """
    Classify the message, route it, run RAG for medical queries,
    update memory, and optionally store/return sources.
    """

    # Get the main LLM used for medical answers.
    qa_llm = get_main_llm()

    # Get the classifier LLM used for intent routing.
    classifier_llm = get_classifier_llm()

    # Normalize the incoming question text.
    q = question.strip()
    lower_q = q.lower()

    # Build the classifier prompt from the user question.
    classifier_prompt = get_classifier_prompt(q)

    # Invoke the classifier chain and extract the classification label string.
    classification = (classifier_prompt | classifier_llm).invoke({"input": ""}).content.strip().lower()

    # Helper function to check if a label is present in the classification string.
    def has_label(label: str) -> bool:
        return label in classification

    # Handle greeting messages.
    if has_label("greeting"):
        return "Hello! How can I help with your medical question?", []

    # Reject non-medical messages politely.
    if has_label("non-medical"):
        return "I can only answer medical or health-related questions.", []
    
    # Handle messages that only ask for sources about previous answers.
    if has_label("source-request"):
        sources = source_manager.get_sources_for_query(q)
        if not sources:
            return "I don’t have any stored sources that match that request.", []
        return "Here are the sources related to that:", sources

    # At this point, the message is expected to be a medical / follow-up type,
    # so we proceed with the normal medical RAG flow.

    # Load the conversation summary and last turn for context.
    summary = summary_memory.load()
    last_user, last_answer = summary_memory.get_last_turn()

    # Build the retrieval query, including summary when available.
    if summary:
        retrieval_query = f"{summary}\nUser: {q}"
    else:
        retrieval_query = q

    # Initialize the retriever with top-k and score threshold.
    retriever = get_retriever(k=4, score_threshold=0.0)

    # Retrieve relevant document chunks for this query.
    retrieved_docs = retriever.invoke(retrieval_query)

    # If no documents are found, signal that there is not enough information.
    return_if_no_docs = "I don’t have enough information in the provided documents to answer that"
    if not retrieved_docs:
        return return_if_no_docs, []

    # Load the prompt template for the medical RAG chain.
    qa_prompt = get_medical_prompt()

    # Prepare all inputs for the document chain.
    chain_input = {
        "classification": classification,
        "summary": summary,
        "last_user": last_user,
        "last_answer": last_answer,
        "input": q,
        "context": retrieved_docs,
    }

    # Create the RAG chain that combines documents and the main LLM.
    doc_chain = create_stuff_documents_chain(qa_llm, qa_prompt)

    # Generate the final medical answer.
    answer = doc_chain.invoke(chain_input).strip()

    # Update the conversation summary with the new turn.
    summary_memory.update(q, answer)

    # Do not process sources if this was not a medical-type label.
    if not (has_label("medical") or has_label("medical-with-sources") or has_label("follow-up")):
        return answer, []

    # Convert answer to lowercase for failure phrase checks.
    lower_ans = answer.lower()

    # List of phrases indicating that the answer could not be completed.
    failure_phrases = [
        "not enough information",
        "insufficient information",
        "i cannot answer",
        "i don't have enough",
        "i dont have enough",
    ]

    # Skip source extraction if the answer reports missing information.
    if any(p in lower_ans for p in failure_phrases):
        return answer, []

    # Use SourceManager to extract a compact sources list from retrieved docs
    # and store this answer and its sources for future source requests.
    sources = source_manager.add_entry_from_docs(q, answer, retrieved_docs)

    # Return answer and sources if the user explicitly asked for sources.
    if has_label("medical-with-sources"):
        return answer, sources

    # Return only the answer for regular medical questions and follow-ups.
    if has_label("medical") or has_label("follow-up"):
        return answer, []

    # Fallback return in case of unexpected label combinations.
    return answer, []
