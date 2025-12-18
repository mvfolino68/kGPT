"""API route modules."""

from kgpt.api.routes.chat import router as chat_router
from kgpt.api.routes.cluster import router as cluster_router
from kgpt.api.routes.documents import router as documents_router
from kgpt.api.routes.settings import router as settings_router

__all__ = ["chat_router", "documents_router", "cluster_router", "settings_router"]
