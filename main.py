"""Main entrypoint for the app."""
import logging
import pickle
from pathlib import Path
from typing import Optional

import pinecone
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain.vectorstores import VectorStore
from langchain.vectorstores.pinecone import Pinecone
from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings

from callback import QuestionGenCallbackHandler, StreamingLLMCallbackHandler
from query_data import get_chain
from schemas import ChatResponse

from constants import (
    EMBEDDING_MODEL,
    EMBEDDING_MODEL_TYPE,
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX,
    VECTORSTORE_TYPE,
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
vectorstore: Optional[VectorStore] = None


@app.on_event("startup")
async def startup_event():
    vectorstore_type = VECTORSTORE_TYPE
    embedding_model_type = EMBEDDING_MODEL_TYPE
    global vectorstore

    logging.info("loading vectorstore")
    if vectorstore_type == "PINECONE":
        if embedding_model_type == "OPENAI":
            embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        elif embedding_model_type == "HUGGINGFACE":
            embeddings = embedding_model_type == HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL
            )
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        index_name = PINECONE_INDEX
        vectorstore = Pinecone.from_existing_index(
            index_name=index_name, embedding=embeddings
        )

    elif vectorstore_type == "FAISS":
        if not Path("vectorstore.pkl").exists():
            raise ValueError(
                "vectorstore.pkl does not exist, please run ingest.py first"
            )
        with open("vectorstore.pkl", "rb") as f:
            vectorstore = pickle.load(f)


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    question_handler = QuestionGenCallbackHandler(websocket)
    stream_handler = StreamingLLMCallbackHandler(websocket)
    chat_history = []
    qa_chain = get_chain(vectorstore, question_handler, stream_handler)
    # Use the below line instead of the above line to enable tracing
    # Ensure `langchain-server` is running
    # qa_chain = get_chain(vectorstore, question_handler, stream_handler, tracing=True)

    while True:
        try:
            # Receive and send back the client message
            question = await websocket.receive_text()
            resp = ChatResponse(sender="you", message=question, type="stream")
            await websocket.send_json(resp.dict())

            # Construct a response
            start_resp = ChatResponse(sender="bot", message="", type="start")
            await websocket.send_json(start_resp.dict())

            result = await qa_chain.acall(
                {"question": question, "chat_history": chat_history}
            )
            chat_history.append((question, result["answer"]))

            end_resp = ChatResponse(sender="bot", message="", type="end")
            await websocket.send_json(end_resp.dict())
        except WebSocketDisconnect:
            logging.info("websocket disconnect")
            break
        except Exception as e:
            logging.error(e)
            resp = ChatResponse(
                sender="bot",
                message="Sorry, something went wrong. Try again.",
                type="error",
            )
            await websocket.send_json(resp.dict())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
