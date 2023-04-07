from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")

# EMBEDDING_MODEL_TYPE = "OPENAI" or "HUGGINGFACE" OpenAI is paid, HuggingFace is free
EMBEDDING_MODEL_TYPE = "HUGGINGFACE"
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

VECTORSTORE_TYPE = "FAISS"

FILTER = [
    "https://docs.confluent.io/platform/current/kafka-rest/production-deployment/confluent-server/config.html"
]
