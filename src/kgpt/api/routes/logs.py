import asyncio
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

# We assume the log file is in the root or same relative location
KAFKA_DEBUG_LOG = "kafka_debug.log"

router = APIRouter(prefix="/logs", tags=["logs"])


@router.websocket("/kafka/ws")
async def websocket_kafka_logs(websocket: WebSocket):
    """
    WebSocket endpoint to stream Kafka debug logs in real-time.
    """
    await websocket.accept()

    # Send initial history
    if os.path.exists(KAFKA_DEBUG_LOG):
        try:
            with open(KAFKA_DEBUG_LOG) as f:
                lines = f.readlines()
                # Send last 50 lines initially
                for line in lines[-50:]:
                    await websocket.send_text(line.strip())
        except Exception as e:
            logger.error(f"Error reading initial logs: {e}")
            await websocket.send_text(f"Error reading history: {str(e)}")

    # Stream new lines
    # We'll implementation a simple tail using file polling
    try:
        f = open(KAFKA_DEBUG_LOG)
        # Seek to end
        f.seek(0, 2)

        while True:
            line = f.readline()
            if line:
                await websocket.send_text(line.strip())
            else:
                # No new line, wait a bit
                await asyncio.sleep(0.1)

            # Check if client is still connected (this might raise)
            # but usually the send_text raises if disconnected.
            # We explicitly check for disconnects via exception handling

    except WebSocketDisconnect:
        logger.info("Client disconnected from log stream")
    except Exception as e:
        logger.error(f"Error in log stream: {e}")
        try:
            await websocket.close()
        except:
            pass
    finally:
        if "f" in locals():
            f.close()
