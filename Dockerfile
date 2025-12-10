FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the embedding model into the image
RUN python -c "from src.config import EMBEDDING_MODEL; \
               from langchain_huggingface import HuggingFaceEmbeddings; \
               HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)"

EXPOSE 5000

CMD ["python", "app.py"]
