# app/control/websocket.py
import json
import logging
import jwt

from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.db.session import SessionLocal

from app.control import models, services


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()
logger = logging.getLogger(__name__)

conn_params = {
    'host': 'localhost',
    'database': 'webcategories_db',
    'user': 'myuser',
    'password': 'mypassword'
}

async def rule_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    user = None

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")

            # 🔹 Authenticate
            if msg_type == "auth":
                token = msg.get("token")
                
                try:
                    decoded = decode_access_token(token)
                    if not decoded:
                        await websocket.close(code=4002)
                        return
                    
                    user_id = decoded["user_id"]
                    user = db.get(models.User, user_id)


                    if not user:
                        await websocket.close(code=4002)
                        return

                    # Clear allowed list on auth
                    services.rules.clear_allowed_list(db, user)

                    await websocket.send_json({"status": "authenticated"})

                    rule = services.rules.get_user_rule(db, user)
                    await websocket.send_json({"type": "rules", "rules": rule})

                except jwt.InvalidTokenError:
                    await websocket.close(code=4002)

            # 🔹 Log blocked URL
            elif msg_type == "log" and user:
                url = msg.get("url")
                if url:
                    services.rules.log_blocked_url(db, user, url)

            # 🔹 Classify domain
            elif msg_type == "classify_domain" and user:
                domain = msg.get("domain")
                if not domain.startswith("http"):
                    domain = "http://" + domain

                # First check PostgreSQL DB
                category = services.rules.get_category_from_db(domain)

                if not category:
                    category = services.utils.scrape_and_categorize(domain)

                is_blocked = services.rules.is_category_blocked(db, user, category)
                services.rules.update_web_categories_db(user, category, domain, is_blocked)

                if not is_blocked:
                    services.rules.add_to_allowed_list(db, user, domain)

                rule = services.rules.get_user_rule(db, user)
                await websocket.send_json({"type": "rules", "rules": rule})

            else:
                await websocket.close(code=4003)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id if user else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4000)
