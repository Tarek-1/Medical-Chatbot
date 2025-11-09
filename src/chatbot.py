# chatbot.py: Core chatbot logic: classifies input, routes to medical QA, or responds politely.

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# From llm_interface.py → provides the Gemini LLM object
from .llm_interface import get_llm          # ← from llm_interface.py

# From retriever.py → provides document retriever connected to Pinecone
from .retriever import get_retriever        # ← from retriever.py

# From prompts.py → provides both the classifier prompt and medical QA prompt templates
from .prompts import get_medical_prompt, get_classifier_prompt  # ← from prompts.py


def answer_question(question):
    """
    Main chatbot pipeline:
        1. Classifies user input as greeting / medical / non-medical.
        2. Greets users politely if it's a greeting.
        3. Answers medical questions using retrieved document context.
        4. Politely refuses non-medical questions.
        5. Includes sources only when context was used.
    """

    # Step 0: Initialize Gemini LLM
    llm = get_llm()                         # ← from llm_interface.py
    q = question.strip()

    # Step 1: Classify input
    classifier_prompt = get_classifier_prompt(q)   # ← from prompts.py
    classification = (classifier_prompt | llm).invoke({"input": ""}).content.strip().lower()

    # Step 2: Greeting
    if "greeting" in classification:
        response = (
            "Hello! 👋 I'm your medical assistant chatbot. "
            "I can only answer medical or health-related questions "
            "based on the provided medical documents. "
            "Please ask a medical question to begin."
        )
        return response, []

    # Step 3: Non-medical
    if "non-medical" in classification:
        response = (
            "I'm a medical chatbot and can only answer medical or health-related questions "
            "based on the medical documents I’ve been provided. "
            "Please ask something related to medicine or healthcare."
        )
        return response, []

    # Step 4: Medical question → Retrieval-Augmented Generation
    retriever = get_retriever(k=3, score_threshold=0.75)   # ← from retriever.py
    docs = retriever.invoke(q)
    if not docs:
        return "I don't have enough information in the provided documents to answer.", []

    qa_prompt = get_medical_prompt()                # ← from prompts.py
    doc_chain = create_stuff_documents_chain(llm, qa_prompt)
    retrieval_chain = create_retrieval_chain(retriever, doc_chain)

    # Step 5: Run pipeline
    response = retrieval_chain.invoke({"input": q})
    answer = response["answer"].strip()

    # Step 6: Extract sources
    sources = []
    if "context" in response and not answer.lower().startswith("i don't have enough information"):
        for doc in response["context"]:
            md = doc.metadata
            sources.append({
                "source": md.get("source"),
                "page": int(md.get("page"))
            })

    return answer, sources
