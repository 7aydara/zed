from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import asyncio
import threading
import queue
import logging

import brain

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    log.info("Client connected to /ws/chat")
    try:
        while True:
            data = await websocket.receive_text()
            log.info(f"UI received text: {data}")
            
            # Since brain.think is a blocking generator, we use a thread and a queue
            # to avoid blocking the asyncio event loop.
            q = queue.Queue()
            
            def producer():
                try:
                    for chunk in brain.think(data):
                        q.put({"type": "chunk", "text": chunk})
                except Exception as e:
                    log.error(f"Brain Error: {e}")
                    q.put({"type": "error", "text": str(e)})
                finally:
                    q.put({"type": "done"})
                    
            t = threading.Thread(target=producer, daemon=True)
            t.start()
            
            # Consume the queue non-blockingly for the websocket
            while True:
                try:
                    msg = q.get_nowait()
                    if msg["type"] == "chunk":
                        await websocket.send_json({"type": "chunk", "text": msg["text"]})
                    elif msg["type"] == "done":
                        await websocket.send_json({"type": "done"})
                        break
                    elif msg["type"] == "error":
                        await websocket.send_json({"type": "error", "text": msg["text"]})
                        break
                except queue.Empty:
                    await asyncio.sleep(0.05)
                    
    except WebSocketDisconnect:
        log.info("Client disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    uvicorn.run("web_server:app", host="127.0.0.1", port=8000, reload=True)
