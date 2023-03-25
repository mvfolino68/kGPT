"""Load html from files, clean up, split, ingest into Weaviate."""
import os
import pickle
from typing import List

import pinecone
from dotenv import load_dotenv
from langchain import OpenAI, VectorDBQA
from langchain.document_loaders import UnstructuredURLLoader
from langchain.embeddings import FakeEmbeddings, HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.vectorstores.pinecone import Pinecone

from sitemap_parser import parseSitemap

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")


def ingest_docs():
    """Get documents from web pages."""
    urls = parseSitemap("https://docs.confluent.io/home/sitemap.xml")
    loader = UnstructuredURLLoader(urls=urls)
    raw_documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
    )
    documents = text_splitter.split_documents(raw_documents)
    # embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    # embeddings = FakeEmbeddings(size=768)

    model_name = "sentence-transformers/all-mpnet-base-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)

    # Save vectorstore
    # initialize pinecone
    # pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

    # index_name = PINECONE_INDEX

    # vectorstore = Pinecone.from_documents(documents, embeddings, index_name=index_name)

    vectorstore = FAISS.from_documents(documents, embeddings)

    # Save vectorstore
    with open("vectorstore.pkl", "wb") as f:
        pickle.dump(vectorstore, f)
    # query = "How Do I Use the Kafka Connect REST API?"
    # docs = vectorstore.similarity_search(query)
    # print(docs[0].page_content)


if __name__ == "__main__":
    ingest_docs()
