# prompts.py: prompt templates for classification, medical RAG, and summary.

from langchain.prompts import PromptTemplate

# CLASSIFIER PROMPT
def get_classifier_prompt(user_msg: str):
    """
    Returns a PromptTemplate for classifying the user message.
    The model must output EXACTLY ONE of these labels:

        greeting
        medical
        medical-with-sources
        follow-up
        source-request
        non-medical
    """

    template = """
You are a strict message classifier. Output EXACTLY ONE label:

- greeting
- medical
- medical-with-sources
- follow-up
- source-request
- non-medical

============================================================
                    CLASSIFICATION RULES
============================================================

1) greeting  
   Trigger words: "hi", "hello", "hey", "good morning", "good evening".

2) medical  
   A new medical or health-related question WITHOUT asking for sources.
   Examples:
     "what is asthma?"
     "symptoms of heart failure"
     "what causes acne"
     "treatment for pneumonia"

3) medical-with-sources  
   The message contains BOTH:
      (A) a medical topic  
      (B) ANY source-related word or phrase  

   This category OVERRIDES ALL OTHER RULES.

   Source-related words/phrases include:
     - sources, source
     - reference, references
     - citation, citations
     - cite, citing
     - page, pages, which page, show page
     - proof, evidence, support
     - documentation, bibliography
     - "give me sources"
     - "with sources"
     - "cite this"
     - "show the pages"
     - "where is that from?"
     - "based on what?"
     - "support this"

   - Any unclear or unusual phrasing that still asks for sources must be treated as medical-with-sources.

   If ANY medical term + ANY source-related keyword appears,
   ALWAYS classify as **medical-with-sources**.

   Examples:
     "what is asthma? give me sources"
     "explain cancer and cite references"
     "female reproductive tract + give me pages"
     "tell me about diabetes with sources"
     "what is heart disease, show me the pages"

4) follow-up  
   The user is referring to the previous answer.
   Examples:
     "continue"
     "explain more"
     "shorter"
     "what about the symptoms?"
     "go on"
     "what else?"

5) source-request  
   The user ONLY wants sources for a PREVIOUS answer,
   and they do NOT introduce a new medical topic.

   Examples:
     "sources?"
     "where did that come from?"
     "show me the references"
     "what were the pages?"
     "cite the last answer"

   IMPORTANT:
     If the user mentions ANY medical topic,
     DO NOT classify as source-request.
     Instead: medical-with-sources.

6) non-medical  
   Anything unrelated to health or medicine.
   Examples:
     "what's the weather"
     "tell me a joke"
     "how old are you"
     "explain quantum physics"

============================================================
                        EXAMPLES
============================================================
"what is asthma? give me sources" → medical-with-sources  
"acoustic neuroma + sources" → medical-with-sources  
"what is the heart? cite pages" → medical-with-sources  
"which page is that from?" → source-request  
"continue" → follow-up  
"what is acoustic neuroma" → medical  
"hello" → greeting  
"tell me a joke" → non-medical

============================================================

User message:
\"\"\"{user_msg}\"\"\"\n
"""

    return PromptTemplate(
        input_variables=["user_msg"],
        template=template,
    ).partial(user_msg=user_msg)

# MEDICAL RAG PROMPT
def get_medical_prompt():
    """Prompt used by the RAG chain for medical QA."""

    template = """
You are a medical QA assistant.

Use ONLY the provided context to answer the question.
If the context is insufficient, say exactly:
"I don't have enough information in the provided documents to answer that."

Classification of user message:
{classification}

Conversation summary:
{summary}

Previous user message:
{last_user}

Previous assistant answer:
{last_answer}

Retrieved medical context (source of truth):
{context}

Current user message:
{input}

---------------- RULES ----------------
- Follow standard medical guidelines.
- Be clear and structured (short paragraphs or bullet points).
- Do NOT invent facts or page numbers.
- If asked about treatment, emphasise that this is not medical advice
  or a diagnosis, and recommend consulting a healthcare professional.
- Do NOT include any section named "Sources", "References", "Bibliography", or anything similar.
- Ignore any "Sources:" or "References:" text inside the context.
- Only provide the medical explanation; the backend will handle sources separately.

Final answer:
"""

    return PromptTemplate(
        input_variables=[
            "classification",
            "summary",
            "last_user",
            "last_answer",
            "context",
            "input",
        ],
        template=template,
    )

# SUMMARY UPDATE PROMPT
def get_summary_prompt():
    """Prompt to maintain a short medically relevant summary."""

    template = """
You maintain a short, medically relevant conversation summary.

Combine:
- Previous summary
- New user message
- New assistant answer

Keep only medically relevant details that may matter for future
questions. Remove greetings, small talk, and unrelated content.

Previous summary:
{prev_summary}

New user message:
{user_message}

New assistant answer:
{assistant_message}

Updated summary:
"""

    return PromptTemplate(
        input_variables=["prev_summary", "user_message", "assistant_message"],
        template=template,
    )
