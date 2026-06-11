# app/main.py
from fastapi import FastAPI, WebSocket,APIRouter,WebSocketDisconnect
from app.control.websocket import rule_websocket
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, logs, rules
from app.control.websocket import rule_websocket
app = FastAPI()

# Mount routers
app.include_router(auth.router)
app.include_router(logs.router)
app.include_router(rules.router)



# Optional: CORS if frontend connects via WebSocket
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] or settings.allowed_hosts,   # restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Normal HTTP route
@app.get("/")
def root():
    return {"message": "FastAPI running"}

# WebSocket route (replacement for Django Channels URLRouter)
@app.websocket("/ws/rules")
async def websocket_endpoint(websocket: WebSocket):
    await rule_websocket(websocket)