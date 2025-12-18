"""Validation agent for checking retrieved document relevance."""

from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from kgpt.agents.state import AgentState, ValidationResult
from kgpt.llm import get_llm

VALIDATION_SYSTEM_PROMPT = """You are a document relevance validator.
Your job is to assess whether a document chunk is relevant to answering a user's question.

You must output a JSON object with:
- "is_relevant": boolean - true if the document helps answer the question
- "confidence": float between 0 and 1 - how confident you are
- "reasoning": string - brief explanation

Be somewhat lenient - if a document provides useful context or background, it's relevant.
Only mark as irrelevant if it's clearly off-topic."""


VALIDATION_USER_PROMPT = """Question: {question}

Document content:
---
{content}
---

Is this document relevant? Respond with JSON only:"""


async def validate_document(question: str, doc: Document) -> ValidationResult:
    """Validate a single document for relevance."""
    try:
        llm = get_llm(streaming=False)
        parser = JsonOutputParser(pydantic_object=ValidationResult)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", VALIDATION_SYSTEM_PROMPT),
                ("human", VALIDATION_USER_PROMPT),
            ]
        )

        chain = prompt | llm | parser

        # Truncate content for validation
        content = doc.page_content[:2000]

        result = await chain.ainvoke(
            {
                "question": question,
                "content": content,
            }
        )

        return result

    except Exception as e:
        logger.warning(f"Validation failed for document: {e}")
        # Default to keeping the document on error
        return {
            "is_relevant": True,
            "confidence": 0.5,
            "reasoning": "Validation failed, keeping document",
        }


async def validation_node(state: AgentState) -> dict:
    """
    Validation node that filters retrieved documents for relevance.

    Checks each document and keeps only relevant ones.
    """
    logger.info(f"Validation agent checking {len(state.get('retrieved_docs', []))} documents...")

    retrieved = state.get("retrieved_docs", [])
    question = state["question"]

    if not retrieved:
        logger.info("No documents to validate")
        return {"validated_docs": []}

    validated: list[Document] = []

    # Validate in batches to avoid rate limits
    for doc in retrieved:
        result = await validate_document(question, doc)

        if result["is_relevant"]:
            doc.metadata["validation_confidence"] = result["confidence"]
            doc.metadata["validation_reasoning"] = result["reasoning"]
            validated.append(doc)
            logger.debug(f"Document validated: confidence={result['confidence']:.2f}")
        else:
            logger.debug(f"Document rejected: {result['reasoning'][:50]}")

    # Sort by validation confidence
    validated.sort(key=lambda d: d.metadata.get("validation_confidence", 0), reverse=True)

    logger.info(f"Validation kept {len(validated)}/{len(retrieved)} documents")

    return {"validated_docs": validated}
