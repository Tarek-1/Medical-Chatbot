# app.py — Flask web app for interactive medical chatbot
# no conversation memory yet.

from flask import Flask, render_template, request, jsonify
from src.chatbot import answer_question
from src.data_loader import prepare_data
from src.config import INDEX_NAME
from pinecone import Pinecone

app = Flask(__name__)

# Temporary in-memory storage for chat display (cleared when server restarts)
chat_history = []


def ensure_index():
    """Check Pinecone index and create it if missing."""
    pc = Pinecone()
    existing_indexes = [index["name"] for index in pc.list_indexes()]
    if INDEX_NAME not in existing_indexes:
        print(f"Index '{INDEX_NAME}' not found — creating and uploading data...")
        prepare_data()
    else:
        print(f"Index '{INDEX_NAME}' found — ready to chat.")


@app.route("/")
def home():
    """Display the main chat UI for user interaction."""
    ensure_index()
    return render_template("index.html", chat_history=chat_history)


@app.route("/ask", methods=["POST"])
def ask():
    """Handle chat requests and return chatbot response."""
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"answer": "Please enter a message.", "sources": []})

    # Run main chatbot pipeline
    answer, sources = answer_question(user_input)

    # Store conversation in temporary memory for UI display
    chat_history.append(("You", user_input))
    chat_history.append(("Bot", answer))
    if sources:
        chat_history.append(("Sources", sources))

    return jsonify({"answer": answer, "sources": sources})


@app.route("/clear", methods=["POST"])
def clear_chat():
    """Clear current in-memory chat history."""
    chat_history.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
