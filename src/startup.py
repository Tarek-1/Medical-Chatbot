# startup.py: runs initialization tasks before the Flask app starts.
# Tasks:
#   - ensure a Pinecone index is available
#   - ingest all PDFs on first run
#   - ingest only new PDFs on later runs

import json
from pathlib import Path
from pinecone import Pinecone

from .config import INDEX_NAME, DATA_PATH
from .data_loader import prepare_data, process_single_pdf


DATA_FOLDER = Path(DATA_PATH)
STATE_FILE = Path("src/processed_docs.json")


# Load list of PDFs that were already ingested previously.
def load_state():
    if not STATE_FILE.exists():
        return []
    with open(STATE_FILE, "r") as f:
        return json.load(f)


# Save updated list of ingested PDFs to disk.
def save_state(processed):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(processed, f, indent=2)


# Check whether the Pinecone index exists.
# If missing, recreate it and ingest all existing PDFs.
def ensure_index():
    pc = Pinecone()
    existing = [idx["name"] for idx in pc.list_indexes()]

    # If Missing index: perform full ingestion
    if INDEX_NAME not in existing:
        print(f"[Startup] Index '{INDEX_NAME}' not found — recreating index + ingesting all PDFs...")

        # Remove old ingestion state to avoid inconsistencies
        if STATE_FILE.exists():
            print("[Startup] Deleting stale processed_docs.json...")
            STATE_FILE.unlink()

        # Process the entire dataset
        prepare_data()

        # Save fresh state containing all PDFs
        all_pdfs = [p.name for p in DATA_FOLDER.glob("*.pdf")]
        save_state(all_pdfs)
        
        return

    print(f"[Startup] Index '{INDEX_NAME}' found — OK.")


# Ingest only new PDF files that were not processed before.
def auto_ingest_new_pdfs():
    processed = load_state()
    all_pdfs = list(DATA_FOLDER.glob("*.pdf"))

    new_files = [p for p in all_pdfs if p.name not in processed]
    if not new_files:
        print("[Startup] No new PDFs detected — skipping incremental ingestion.")
        return

    print(f"[Startup] New PDFs detected: {[p.name for p in new_files]}")

    for pdf_path in new_files:
        try:
            print(f"[Startup] Ingesting new PDF: {pdf_path.name}")
            process_single_pdf(pdf_path)
            processed.append(pdf_path.name)
            save_state(processed)
            print(f"[Startup] Finished: {pdf_path.name}")
        except Exception as e:
            print(f"[Startup] Error while processing {pdf_path.name}: {e}")


# Run all initialization steps before the web server starts.
def run_startup():
    print("=== Startup: initialization begin ===")
    ensure_index()
    auto_ingest_new_pdfs()
    print("=== Startup: initialization complete ===")
