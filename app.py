# app.py: Flask web app that serves the medical chatbot UI and API

from flask import Flask, render_template, request, jsonify
from src.chatbot import answer_question
from src.startup import run_startup

app = Flask(__name__)

# In-memory chat log for the UI (not used by the RAG system)
chat_history = []


@app.route("/")
def home():
    """Render the frontend chat interface."""
    return render_template("index.html", chat_history=chat_history)


@app.route("/ask", methods=["POST"])
def ask():
    """Receive a user message, generate an answer, and return it as JSON."""
    data = request.get_json()
    user_input = data.get("message", "").strip()

    # Basic input validation
    if not user_input:
        return jsonify({"answer": "Please enter a message.", "sources": []})

    # Core chatbot logic
    answer, sources = answer_question(user_input)

    # Append conversation to UI history (frontend only)
    chat_history.append(("You", user_input))
    chat_history.append(("Bot", answer))
    if sources:
        chat_history.append(("Sources", sources))

    # API response to frontend
    return jsonify({"answer": answer, "sources": sources})


@app.route("/clear", methods=["POST"])
def clear_chat():
    """Reset the temporary UI-only chat history."""
    chat_history.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    # Run ingestion, indexing, and initialization steps once at startup
    run_startup()

    # Start the Flask server
    app.run(host="0.0.0.0", port=5000, debug=True)
