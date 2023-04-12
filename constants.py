from dotenv import load_dotenv
import os

load_dotenv()

VECTORSTORE_TYPE = "FAISS"  # "FAISS" or "PINECONE"

# Set Pinecone API Variables if you want to use Pinecone
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")

# Set these variables if you want to use HuggingFace (free) instead of OpenAI (paid)
# EMBEDDING_MODEL_TYPE = "OPENAI" or "HUGGINGFACE" OpenAI is paid, HuggingFace is free
EMBEDDING_MODEL_TYPE = "HUGGINGFACE"
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"


# Set Azure API Variables if you want to use Azure
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_TYPE = os.environ["OPENAI_API_TYPE"]

# This can change depending on the model you are using
# More info: https://learn.microsoft.com/en-us/azure/cognitive-services/openai/chatgpt-quickstart?tabs=command-line&pivots=programming-language-python
OPENAI_API_VERSION = os.environ["OPENAI_API_VERSION"]
AZURE_OPENAI_MODEL = os.environ["AZURE_OPENAI_MODEL"]

# Set these variables if you want to use Azure
# More info: https://docs.microsoft.com/en-us/azure/cognitive-services/openai/quickstarts/quickstart-sdk
# And here: https://python.langchain.com/en/latest/modules/models/llms/integrations/azure_openai_example.html
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE")
AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
