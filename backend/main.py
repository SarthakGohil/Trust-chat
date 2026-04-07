from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
try:
    from .database import messages_collection, init_db
    from .ml import analyze_message
except ImportError:
    from database import messages_collection, init_db
    from ml import analyze_message
from datetime import datetime
import asyncio
import json
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI()
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["*"], allow_headers=["*"])

active_connections = {}

@app.on_event("startup")
async def _startup():
    init_db()

@app.get("/health")
async def health(): return {"status": "ok"}

# API Routes
@app.get("/api/messages/{u1}/{u2}")
async def get_history(u1: str, u2: str):
    query = {"$or": [{"sender": u1, "receiver": u2}, {"sender": u2, "receiver": u1}]}
    try:
        msgs = list(messages_collection.find(query).sort("timestamp", -1).limit(50))
    except Exception:
        return []
    for m in msgs: m["_id"] = str(m["_id"])
    return msgs[::-1]

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)
            msg_obj = {
                "sender": username, "receiver": msg_data["receiver"],
                "text": msg_data["text"], "timestamp": datetime.utcnow(),
                "emotion": None, "trust_score": None, "is_sarcasm": None,
                "client_id": msg_data.get("client_id")
            }
            inserted_id = None
            try:
                res = messages_collection.insert_one(msg_obj)
                inserted_id = res.inserted_id
            except Exception:
                inserted_id = None

            payload_id = str(inserted_id) if inserted_id else (msg_obj.get("client_id") or "")
            payload = {**msg_obj, "_id": payload_id, "timestamp": msg_obj["timestamp"].isoformat()}
            for target in [username, msg_data["receiver"]]:
                ws = active_connections.get(target)
                if ws:
                    try:
                        await ws.send_text(json.dumps(payload))
                    except Exception:
                        active_connections.pop(target, None)

            async def enrich_and_broadcast():
                analysis = await analyze_message(msg_data["text"])
                if inserted_id:
                    try:
                        messages_collection.update_one({"_id": inserted_id}, {"$set": analysis})
                    except Exception:
                        return
                updated = {**payload, **analysis}
                for target in [username, msg_data["receiver"]]:
                    ws2 = active_connections.get(target)
                    if ws2:
                        try:
                            await ws2.send_text(json.dumps(updated))
                        except Exception:
                            active_connections.pop(target, None)

            asyncio.create_task(enrich_and_broadcast())
    except WebSocketDisconnect:
        active_connections.pop(username, None)

# Serve Frontend (Static Files)
# This will be used in unified deployments like Hugging Face or Koyeb
dist_path = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(dist_path / "index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
