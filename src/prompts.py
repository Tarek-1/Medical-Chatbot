# prompts.py: Defines the prompt templates used by the chatbot

from langchain_core.prompts import ChatPromptTemplate

# ==============================================================
# 1. CLASSIFIER PROMPT
# --------------------------------------------------------------
#   - Determines what type of message the user sent.
#   - Helps the chatbot decide whether to greet, answer medically, or refuse politely.
# ==============================================================
def get_classifier_prompt(user_message: str):
    return ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a message classifier for a medical chatbot. "
            "Categorize the user's message into one of three types: "
            "'greeting', 'medical', or 'non-medical'. "
            "Consider as 'medical' anything related to medicine, healthcare, "
            "diseases, anatomy, physiology, biology of the human body, symptoms, "
            "treatments, drugs, or medical terminology. "
            "Only return one word: greeting, medical, or non-medical."
        ),
        ("human", f"{user_message}")
    ])


# ==============================================================
# 2. MEDICAL QA PROMPT
# --------------------------------------------------------------
#   - Guides the LLM to answer medical questions strictly based on
#     retrieved document context from Pinecone.
#   - Prevents hallucinations by requiring the model to rely only on context.
# ==============================================================
def get_medical_prompt():
    system_prompt = (
        "You are a helpful and factual medical assistant. "
        "Use only the retrieved context from medical documents to answer the question. "
        "If the documents do not contain enough relevant information, reply with: "
        "'I don't have enough information in the provided documents to answer.' "
        "Keep answers concise and medically accurate.\n\n{context}"
    )

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
