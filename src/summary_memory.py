# summary_memory.py: maintains a short medical conversation summary.

from .prompts import get_summary_prompt
from .llm_interface import get_summary_llm


class SummaryMemory:
    """
    Tracks lightweight conversational state, including:
        - a compact summary of medically relevant information
        - the most recent user message
        - the most recent assistant answer

    Keeps the RAG system context-aware without storing full chat history.
    """

    def __init__(self):
        # Rolling summary of the conversation
        self.conversation_summary = ""
        # Last user message and last generated answer
        self.last_user = None
        self.last_answer = None


    # Return the current summary for retrieval queries
    def load(self) -> str:
        return self.conversation_summary

    # Return the most recent QA pair for follow-up questions
    def get_last_turn(self):
        return self.last_user, self.last_answer
    
    # Update the stored summary and last turn data
    def update(self, user_message: str, assistant_message: str):
        """
        Updates the summary only when the assistant produced a
        valid medical answer. Skips updates for failure messages
        to prevent polluting the conversation state.
        """
        if (not assistant_message or "not have enough information" in assistant_message.lower()):
            return

        summary_prompt = get_summary_prompt()
        llm = get_summary_llm()

        # Build the chain that creates the updated summary
        new_summary_chain = summary_prompt | llm

        updated = new_summary_chain.invoke({
            "prev_summary": self.conversation_summary,
            "user_message": user_message,
            "assistant_message": assistant_message,
        }).content.strip()

        # Save updated summary and last turn
        self.conversation_summary = updated
        self.last_user = user_message
        self.last_answer = assistant_message
