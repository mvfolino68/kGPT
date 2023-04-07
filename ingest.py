import pickle

import nest_asyncio
import pinecone
from langchain.document_loaders.sitemap import SitemapLoader
from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.vectorstores.pinecone import Pinecone

from constants import (
    EMBEDDING_MODEL,
    EMBEDDING_MODEL_TYPE,
    FILTER,
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX,
    VECTORSTORE_TYPE,
)

nest_asyncio.apply()


def ingest_docs(
    vectorstore_type=VECTORSTORE_TYPE, embedding_model_type=EMBEDDING_MODEL_TYPE, filter=FILTER
):
    """Ingest documents from Confluent docs into a vectorstore"""
    sitemap_loader = SitemapLoader(
        web_path="https://docs.confluent.io/home/sitemap.xml"
    )
    raw_documents = sitemap_loader.load()

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
    )
    documents = text_splitter.split_documents(raw_documents)

    # Create Embeddings
    if embedding_model_type == "HUGGINGFACE":
        # Use hugging face embeddings for free
        model_name = EMBEDDING_MODEL
        embeddings = HuggingFaceEmbeddings(model_name=model_name)

    elif embedding_model_type == "OPENAI":
        # Use OpenAI embeddings at a cost
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    # Create vectorstore
    if vectorstore_type == "PINECONE":
        # Uinitialize Pinecone and create index
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        index_name = PINECONE_INDEX
        vectorstore = Pinecone.from_documents(
            documents, embeddings, index_name=index_name
        )

    elif vectorstore_type == "FAISS":
        # Use FAISS vectorstore
        vectorstore = FAISS.from_documents(documents, embeddings)

        # Save FAISS vectorstore
        with open("vectorstore.pkl", "wb") as f:
            pickle.dump(vectorstore, f)


if __name__ == "__main__":
    ingest_docs()
