# Medical Chatbot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Backend](https://img.shields.io/badge/Backend-Flask-green.svg)
![Technique](https://img.shields.io/badge/Technique-RAG-yellow.svg)
![VectorDB](https://img.shields.io/badge/VectorDB-Pinecone-purple.svg)
![LLM](https://img.shields.io/badge/LLM-Gemini-blueviolet.svg)
![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)


A Retrieval Augmented Generation (RAG) medical chatbot that provides accurate, source-grounded medical answers using your own uploaded medical textbooks and PDF documents.  
The system combines **Pinecone** vector search, **Google Gemini**, **LangChain**, and **Hugging Face embeddings** into a clean, modular architecture that is easy to run, extend, and use through a modern web UI or a simple HTTP API.

Unlike typical chatbots, this system always retrieves from your PDFs first, then generates an answer backed by real pages and books.

---

## Overview

The project is built for the use case:

> "I want to ask medical questions and see exactly which books and pages the answer came from."

Core ideas:

- Store medical PDFs in a vector database
- Retrieve relevant chunks for each question
- Generate an answer using a medical-focused prompt
- Extract and store book names and page ranges used in each answer
- Allow the user to ask for sources later, such as "sources?" or "which page?"

All of the document ingestion and indexing is handled automatically when the server starts.

---

## Features

### Accurate medical answers based on your PDFs

For each medical question the chatbot:

1. Builds a retrieval query using the current question and a short summary of the conversation
2. Uses Pinecone to retrieve the most relevant chunks from your indexed PDFs
3. Sends those chunks plus the question to the RAG chain
4. Generates an answer that is grounded on the retrieved content

### Automatic source extraction and page ranges

For every answer, the system:

- Reads `source` and `page` metadata from each retrieved document
- Groups pages by book
- Sorts pages and removes duplicates
- Merges consecutive pages into human-friendly ranges  
  Example: `[10, 11, 12, 20, 22, 23]` becomes `"10 to 12"` and `"22 to 23"`
- Stores these sources together with the question and answer

Later the user can ask `"sources?"`, `"what page?"`, or `"where did this come from"` and get a clear list of books and pages that were actually used.

### Input classification and routing

A small classifier language model labels each incoming message as:

- greeting  
- medical  
- medical with sources  
- follow up  
- source request  
- non medical  

`chatbot.py` uses this label to decide what to do:

- **Greeting**: return a simple greeting answer  
- **Non medical**: explain that only medical or health-related questions are supported  
- **Source request**: look up sources from `SourceManager`  
- **Medical / follow up**: run the full RAG pipeline  

This keeps routing logic explicit and easy to modify.

### Short term conversation memory

`SummaryMemory` keeps:

- A compact text summary of the medically relevant conversation so far
- The last user message
- The last assistant answer

This gives the system enough context to handle follow-up questions, such as:

> "What are the treatments?" right after "What is acne"

without storing or re-sending the whole chat history.

### Source history and semantic lookup

`SourceManager` stores, for each answer:

- The original user question
- The answer text
- The list of sources and page ranges
- An embedding of `question + answer`

Later, when the user asks for sources, the system can:

- Return the latest entry for simple queries such as `"sources?"`
- Use semantic similarity to find the most relevant past answer for more detailed source questions, such as  
  `"What books did you use for the iron deficiency explanation?"`

### Automatic startup indexing

When you run `python app.py`, the application imports the startup logic which:

- Checks whether the Pinecone index exists and creates it if needed
- Loads metadata about previously processed documents from `processed_docs.json`
- Scans the data folder for PDF files
- Detects which PDFs are new or changed
- Runs the data loading and embedding **only** for new or updated content
- Updates the Pinecone index

This makes startup safe to run every time and avoids re-embedding everything on each run.

### Docker support

The project includes a Dockerfile so you can run the whole system inside a container.  
This avoids dependency issues and makes it easy to move the app between machines or servers.

---

## Tech Stack

### Backend

- **Flask** for the HTTP API and web server
- **LangChain** for orchestration of the RAG pipeline
- **Google Gemini** for:
  - Medical answer generation
  - Message classification
  - Conversation summarization

### Retrieval and embeddings

- **Pinecone** as the vector database
- **HuggingFaceEmbeddings** with `BAAI/bge-m3` as the embedding model  
  (Used both for document embeddings and for source-history similarity)

### Document processing

- **PyMuPDF**  for PDF parsing and page handling
- Custom / configured text splitting logic for high-quality chunks that work well with embeddings

### Frontend

- HTML + CSS for the layout and styling
- JavaScript (`script.js`) for chat logic

### Utilities

- **NumPy** for numerical work
- **scikit-learn** for cosine similarity and related operations
- `uuid4` (reserved for future use as stable IDs if source history is stored in a database)


---

## Prerequisites

You need:

- Python 3.10 or newer
- A Google API key with access to Gemini
- A Pinecone API key and an existing index name
- A set of medical PDFs that are text based and not encrypted
- Docker if you want container based execution

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/medical-chatbot
cd medical-chatbot
```

### 2. Create and activate a Conda environment

```bash
conda create -n medical_chatbot python=3.10 -y
conda activate medical_chatbot
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a file named `.env` in the project root with content similar to

```env
GOOGLE_API_KEY=your_google_key
PINECONE_API_KEY=your_pinecone_key
```

### 5. Put your PDFs in the data folder

Place your medical PDFs in the `data/` directory.  
The startup logic will read from this folder when the server starts.

### 6. Start the Flask server

```bash
python app.py
```

On the first run the server will take longer to start while it

- Creates the Pinecone index if it does not exist
- Processes the PDFs in `data/`
- Stores embeddings in Pinecone
- Writes `processed_docs.json` with information about what was indexed

On later runs it will only embed new or changed files.

By default the API listens on

```
http://127.0.0.1:5000
```

---

## Running with Docker

### Build the image

```bash
docker build -t medical_chatbot .
```

### Run the container

```bash
docker run -p 5000:5000 medical-chatbot
```

The application will be available at

```
http://localhost:5000
```

The same automatic startup logic runs inside the container.  
On the first start it will create the index and embed all PDFs.  
On later starts it will only process new or changed files.

---

## API Usage

The backend exposes:

- A **browser UI** at:
  - `GET /` → renders the chat interface (HTML)
- A **main API endpoint** at:
  - `POST /ask` → send questions and receive answers
- A **utility endpoint** at:
  - `POST /clear` → clear in-memory chat history (used by the UI’s “Clear chat” button)

### `/ask` request and response

- URL: `/ask`  
- Method: `POST`  
- Request body type: JSON  
- Required field: `message` (string with the user question)

The response is also JSON and always has:

- `answer` (string): what the chatbot says  
- `sources` (list): zero or more objects of the form  
  `{ "source": "<file name>", "page": "<page or range>" }`

If the user does not explicitly ask for sources, `sources` will usually be an empty list (but the system will still store them internally so they can be retrieved later).

---

### Example 1: basic medical question (answer only)

User sends a question. No mention of sources.

Request body:

```json
{
  "message": "What are the symptoms of iron deficiency?"
}
```

Possible response:

```json
{
  "answer": "Iron deficiency anemia commonly presents with fatigue, pallor, reduced exercise tolerance, shortness of breath on exertion, and sometimes pica. In more severe or chronic cases, patients may have brittle nails, hair loss, glossitis, or restless legs.",
  "sources": []
}
```

Explanation:

- The backend retrieved relevant pages from your PDFs.
- It used them to build the answer.
- The user did not ask for sources, so `sources` is an empty list.

---

### Example 2: ask for answer and sources in one step

Here the user explicitly asks for sources in the same message.

Request body:

```json
{
  "message": "What is acne and give me sources"
}
```

Possible response:

```json
{
  "answer": "Acne vulgaris is a chronic inflammatory disease of the pilosebaceous unit that presents with comedones, papules, pustules and sometimes nodules on the face, chest, and back. It is driven by follicular hyperkeratinization, increased sebum production, Cutibacterium acnes colonization, and inflammation.",
  "sources": [
    { "source": "Dermatology_Textbook.pdf", "page": "112 to 115" },
    { "source": "Harrison_Internal_Medicine.pdf", "page": "890" }
  ]
}
```

Explanation:

- The classifier detects that the message is a medical question with a request for sources.
- The system returns both:
  - `answer`: the medical explanation  
  - `sources`: a list of book and page ranges that were used

---

### Example 3: ask for sources later (follow up source request)

Sometimes the user wants the answer first, and the sources later.

Step 1: user asks the question:

```json
{
  "message": "What is acne?"
}
```

The system answers without sources:

```json
{
  "answer": "Acne vulgaris is a chronic inflammatory disease of the pilosebaceous unit that presents with comedones, papules, pustules and sometimes nodules on the face, chest, and back. It is driven by follicular hyperkeratinization, increased sebum production, Cutibacterium acnes colonization, and inflammation.",
  "sources": []
}
```

Step 2: user asks for sources only:

```json
{
  "message": "sources?"
}
```

Possible response:

```json
{
  "answer": "Here are the sources related to that:",
  "sources": [
    { "source": "Dermatology_Textbook.pdf", "page": "112 to 115" }
  ]
}
```

Explanation:

- Short messages like `"sources?"` or `"which page?"` are treated as a pure source request.
- The backend looks at the most recent stored answer in `SourceManager`.
- It returns the sources that were saved for that last medical answer.

For more complex source questions, such as:

```json
{
  "message": "What books did you use for the explanation about iron deficiency?"
}
```

the system can use semantic similarity on past answers to find the closest matching answer and return the sources for that specific topic.

---

## Internal Architecture

### High level pipeline

1. A user message arrives at the Flask endpoint (`/ask` from the UI or your client).
2. `answer_question` in `chatbot.py` calls the classifier language model.
3. Based on the label, the function either:  
   - returns a greeting  
   - rejects non-medical content  
   - serves a source request through `SourceManager`  
   - runs the RAG pipeline for medical and follow-up questions  
4. For RAG:  
   - Build a retrieval query using the current question and conversation summary  
   - Use `retriever.py` to query Pinecone and get document chunks  
   - Pass chunks plus metadata to the LangChain RAG chain and generate an answer  
5. Update `SummaryMemory` with the new turn  
6. Extract sources from retrieved documents and store them through `SourceManager`  
7. Return the answer and, if requested, the sources

## Module Overview

### `app.py`
Flask entry point.  
- Serves the web UI at `/`  
- Exposes `/ask` and `/clear` endpoints  
- Runs startup indexing logic on launch  

### `chatbot.py`
Core orchestration logic:
- message classification  
- retrieval  
- RAG generation  
- memory update  
- source extraction and storage  

### `retriever.py`
Handles Pinecone vector search:
- index configuration  
- retrieval parameters (`k`, score thresholds)  
- fetches relevant chunks for RAG  

### `source_manager.py`
Stores:
- each question + answer  
- extracted sources (pages, merged ranges)  
- embeddings for semantic source lookup  

Provides:
- simple source lookup (`sources?`)  
- semantic matching for detailed source questions  

### `summary_memory.py`
Maintains a compact conversation memory:
- short running summary  
- last user message  
- last assistant answer  

Supports follow-up question understanding without storing full history.

### `llm_interface.py`
Unified interface to Google Gemini models:
- classifier LLM  
- summarizer LLM  
- main medical-answer LLM  

Keeps model usage in one place for easier upgrades.

### `prompts.py`
All system prompts for:
- classification  
- summarization  
- medical RAG answer generation  

### `data_loader.py`
Responsible for PDF ingestion:
- loads PDFs using PyMuPDF  
- cleans extracted text  
- splits into chunks  
- embeds chunks  
- writes embeddings to Pinecone  

### `startup.py`
Runs once on application start:
- checks Pinecone index  
- detects new/changed PDFs  
- triggers re-embedding only where needed  

### `config.py`
Central configuration:
- model names  
- index name  
- chunking parameters  
- data paths  

---

## Additional Files

### `Dockerfile`
Defines a reproducible environment for running the entire application inside Docker:
- installs dependencies  
- sets up Python runtime  
- configures container startup command  

### `requirements.txt`
Lists all Python package dependencies required for the project.

### `processed_docs.json`
A tracking file generated automatically during startup. It stores metadata about each PDF that has already been processed, such as file name, modified timestamp, and number of chunks. This allows the startup process to detect which PDFs are new or changed and skip reprocessing unchanged documents. This file is managed internally by the system and should not be edited manually.

### `template.sh`
A setup script used for creating the initial project folder structure and placeholder files. Running this script generates directories such as src/, templates/, static/, and creates empty files like .env, setup.py, and requirements.txt. It is intended to be run once when scaffolding a new development environment.

### `.env`
A private environment file that stores API keys and configuration values, for example:

GOOGLE_API_KEY=your_key
PINECONE_API_KEY=your_key

The application loads these values at runtime so credentials do not appear in the source code or version control.

---

# Planned Enhancements

### 1. Multi-Topic Memory
**Problem:**  
The system keeps a single running summary, which causes loss of context whenever the user changes medical topics.

**Direction:**  
Introduce a memory structure that maintains a separate summary for each topic. The system will detect the topic of each message and update only the relevant summary. This allows users to move between topics without losing previous context and sets the foundation for more advanced long-term memory.

---

### 2. Stronger Retrieval for RAG
**Problem:**  
A single retrieval attempt may miss relevant information, especially when users phrase questions differently from the way medical content appears in textbooks.

**Direction:**  
Improve retrieval by generating several alternative versions of the user’s question, gathering results from each version, and ranking the retrieved passages to keep only the most relevant ones. This produces more accurate grounding and more reliable medical answers.

---

### 3. Per-User Memory
**Problem:**  
All users currently share one global memory. This mixes conversations together and prevents personalization. It works on a local machine but becomes a major limitation once deployed for multiple visitors.

**Direction:**  
Assign each visitor a unique identifier so every user receives an isolated memory that contains only their topics and summaries. This design supports multi-user deployments and can evolve into persistent user profiles that maintain context across sessions and devices.

---

### 4. Persistence
**Problem:**  
All memory is lost when the server restarts, which prevents long-term conversational continuity.

**Direction:**  
Add a lightweight database to store users, topics, and message histories so memory can be restored automatically on startup. This enables durable context and long-term interactions.

---

### 5. Advanced PDF and Image Understanding
**Problem:**  
The current ingestion pipeline extracts only plain text. It does not understand tables or images. As a result, diagrams, charts, X-rays, and other visual content in medical PDFs are ignored, which limits retrieval accuracy and prevents the system from using important visual information.

**Direction:**  
Upgrade the ingestion pipeline to use an AI-based document parser that can interpret both text and images. The improved system should be able to:

- Detect and preserve table structure instead of treating it as random text  
- Understand comparisons, rows, and columns inside tables  
- Interpret medical images and diagrams even when no text is present  
- Convert what it understands into a format that can be stored and retrieved alongside normal text  

The goal is to enable true multimodal retrieval, where both written information and visual medical content contribute to more accurate answers.

---

### 6. Prompt Optimization and Evaluation
**Problem:**  
The system relies on several prompts that guide classification, retrieval, and answer generation. Testing has already helped refine these prompts, but additional evaluation is needed to identify edge cases and further strengthen consistency.

**Direction:**  
Continue refining prompts through regular testing. When the model shows confusion, weak grounding, or any unexpected behavior, the prompts will be adjusted to make responses clearer and more reliable. This ongoing process will steadily improve accuracy and consistency across all medical questions.
