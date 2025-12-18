"""Logging configuration for kGPT."""

import sys

from loguru import logger

from kgpt.config import settings


def setup_logging():
    """Configure loguru logging for the application."""
    # Remove default handler
    logger.remove()

    # Console handler with color
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=log_format,
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
    )

    # File handler for persistent logs
    log_dir = settings.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "kgpt_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="1 day",
        retention="7 days",
        compression="zip",
    )

    logger.info("Logging configured")


def log_agent_step(agent_name: str, action: str, details: dict = None):
    """Log an agent step for observability."""
    msg = f"[{agent_name}] {action}"
    if details:
        msg += f" | {details}"
    logger.info(msg)


def log_query(question: str, answer_length: int, citations: int, duration_ms: float):
    """Log a completed query for analytics."""
    logger.info(
        f"Query completed | "
        f"question_length={len(question)} | "
        f"answer_length={answer_length} | "
        f"citations={citations} | "
        f"duration_ms={duration_ms:.1f}"
    )
