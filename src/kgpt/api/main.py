from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Load environment variables immediately before local imports
load_dotenv()

from kgpt.api.routes import (
    chat_router,
    cluster_router,
    documents_router,
    logs_router,
    settings_router,
)
from kgpt.api.schemas import HealthResponse
from kgpt.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    setup_logging()
    logger.info("kGPT API starting up...")

    # Ensure data directory exists
    from kgpt.config import settings

    settings.ensure_data_dir()

    # Initialize database
    from kgpt.db import get_db

    db = get_db()
    logger.info("Database initialized")

    # Restore active Kafka cluster context if one was previously connected
    active_cluster = db.get_active_kafka_cluster()
    if active_cluster:
        from kgpt.services.kafka import get_kafka_service

        try:
            config = {
                "name": active_cluster["name"],
                "bootstrap_servers": active_cluster["bootstrap_servers"],
                "security_protocol": active_cluster.get("security_protocol", "PLAINTEXT"),
                "sasl_mechanism": active_cluster.get("sasl_mechanism"),
                "sasl_username": active_cluster.get("sasl_username"),
                "sasl_password": active_cluster.get("sasl_password"),
            }

            service = get_kafka_service()
            service.set_config(config)

            # Test connection before considering it restored
            try:
                service.test_connection()
                logger.info(f"Restored Kafka cluster context: {active_cluster['name']}")
            except Exception as e:
                logger.warning(f"Could not restore Kafka cluster: {e}")
        except Exception as e:
            logger.warning(f"Failed to restore Kafka cluster context: {e}")

    yield

    # Shutdown
    logger.info("kGPT API shutting down...")


app = FastAPI(
    title="kGPT API",
    description="A modern multi-agent documentation assistant for Kafka and Confluent",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
        "http://localhost:3000",  # Alternative dev port
        "http://frontend:3000",  # Docker network
        "http://127.0.0.1:5173",  # Vite dev server (127.0.0.1)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(cluster_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(logs_router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Check the health of the API and its dependencies."""
    from kgpt.services.kafka import get_kafka_service
    from kgpt.vectorstore import get_vectorstore

    # Check Qdrant
    qdrant_connected = False
    try:
        store = get_vectorstore()
        qdrant_connected = store.health_check()
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")

    # Check Kafka
    kafka_connected = get_kafka_service().config is not None

    return HealthResponse(
        status="healthy" if qdrant_connected else "degraded",
        version="2.0.0",
        qdrant_connected=qdrant_connected,
        kafka_connected=kafka_connected,
    )


@app.get("/")
async def root():
    """Root endpoint - redirect to docs or return basic info."""
    return {
        "name": "kGPT API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


def run():
    """Run the API server."""
    import uvicorn

    uvicorn.run(
        "kgpt.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
