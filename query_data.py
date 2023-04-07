"""Create a ChatVectorDBChain for question/answering."""
import os
from typing import List

from langchain.callbacks.base import AsyncCallbackManager
from langchain.callbacks.tracers import LangChainTracer
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT
from langchain.chains.llm import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import Document
from langchain.vectorstores.base import VectorStore, VectorStoreRetriever
from pydantic import Field


async def aget_relevant_documents(self, query: str) -> List[Document]:
    return self.get_relevant_documents(query)


VectorStoreRetriever.aget_relevant_documents = aget_relevant_documents

doc_template = """--- document start ---
content:{page_content}
--- document end ---
"""

CONFLUENT_DOC_PROMPT = PromptTemplate(
    template=doc_template, input_variables=["page_content"]
)

prompt_template = """You are an AI assistant for Confluent and Kafka documentation. 
You are given the following extracted parts of a long document and a question. Your task is to answer the question the best you can. Pretend you are a human answering the question.
The docs may not have an exact answer to the question, but you should try to answer the question as best you can. Your job is to help the user find the answer to the question.
If the question includes a request for code, provide a fenced code block directly from the documentation.
Question: {question}
Documents:
=========
{context}
=========
Answer in Markdown:"""

# QA_PROMPT = PromptTemplate(
#     template=prompt_template, input_variables=["context", "question"]
# )


def get_chain(
    vectorstore: VectorStore, question_handler, stream_handler, tracing: bool = False
) -> ConversationalRetrievalChain:
    """Create a ConversationalRetrievalChain for question/answering."""
    # Construct a ConversationalRetrievalChain with a streaming llm for combine docs
    # and a separate, non-streaming llm for question generation
    manager = AsyncCallbackManager([])
    question_manager = AsyncCallbackManager([question_handler])
    stream_manager = AsyncCallbackManager([stream_handler])
    if tracing:
        tracer = LangChainTracer()
        tracer.load_default_session()
        manager.add_handler(tracer)
        question_manager.add_handler(tracer)
        stream_manager.add_handler(tracer)

    question_gen_llm = OpenAI(
        model_name="gpt-3.5-turbo",
        max_tokens=1000,
        temperature=0,
        verbose=True,
        callback_manager=question_manager,
    )
    streaming_llm = ChatOpenAI(
        streaming=True,
        callback_manager=stream_manager,
        verbose=True,
        temperature=0,
    )
    question_generator = LLMChain(
        llm=question_gen_llm, prompt=CONDENSE_QUESTION_PROMPT, callback_manager=manager
    )
    doc_chain = load_qa_chain(
        streaming_llm, chain_type="stuff", 
        # prompt=QA_PROMPT, 
        callback_manager=manager
    )

    qa = ConversationalRetrievalChain(
        retriever=vectorstore.as_retriever(),
        combine_docs_chain=doc_chain,
        question_generator=question_generator,
        callback_manager=manager,
    )

    return qa
