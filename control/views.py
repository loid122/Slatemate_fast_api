from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status, HTTPException
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from typing import List
import psycopg

from .models import Rule, Log, User   # SQLAlchemy models you’ll define
from app.db.session import SessionLocal
from app.control.websocket import manager   # if you want to track connections


router = APIRouter()

# PostgreSQL connection params
conn_params = {
    'host': 'localhost',
    'dbname': 'webcategories_db',
    'user': 'myuser',
    'password': 'mypassword'
}

# ---------- Schemas ----------
class LoginSchema(BaseModel):
    username: str
    password: str

class RuleSchema(BaseModel):
    websites: List[str]
    words: List[str]
    categories: List[str]

class LogSchema(BaseModel):
    url: str

# ---------- LOGIN ----------
@router.post("/login")
def login(data: LoginSchema, Authorize: AuthJWT = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = Authorize.create_access_token(subject=str(user.id))
    refresh_token = Authorize.create_refresh_token(subject=str(user.id))
    return {"access": access_token, "refresh": refresh_token}

# ---------- RULES ----------
@router.post("/rules")
def update_rules(data: RuleSchema, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()

    expanded_websites = list(data.websites)

    try:
        conn = psycopg.connect(**conn_params)
        c = conn.cursor()

        for category in data.categories:
            c.execute("SELECT id FROM Categories WHERE category_name = %s", (category,))
            row = c.fetchone()
            if row:
                category_id = row[0]
                c.execute("SELECT website_name FROM Websites WHERE category_id = %s", (category_id,))
                expanded_websites.extend([r[0] for r in c.fetchall()])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        c.close()
        conn.close()

    expanded_websites = list(set(expanded_websites))

    db = SessionLocal()
    rule = db.query(Rule).filter(Rule.user_id == user_id).first()
    if not rule:
        rule = Rule(user_id=user_id)

    rule.words = data.words
    rule.websites = expanded_websites
    rule.categories = data.categories
    rule.allowed_list = []

    db.add(rule)
    db.commit()

    # Push to WebSocket clients
    rules_payload = {
        "words": rule.words,
        "websites": rule.websites,
        "categories": rule.categories,
        "allowed_list": rule.allowed_list
    }
    manager.broadcast(user_id, rules_payload)

    return {"message": "Rules updated and pushed successfully"}

@router.get("/rules")
def get_rules(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()

    db = SessionLocal()
    rule = db.query(Rule).filter(Rule.user_id == user_id).first()

    if not rule:
        return {"rules": {"websites": [], "words": [], "categories": [], "allowed_list": []}}

    return {"rules": {
        "websites": rule.websites,
        "words": rule.words,
        "categories": rule.categories,
        "allowed_list": rule.allowed_list
    }}

# ---------- LOGS ----------
@router.post("/logs")
def create_log(data: LogSchema, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()

    db = SessionLocal()
    log = Log(user_id=user_id, url=data.url[:2048])
    db.add(log)
    db.commit()

    return {"message": "Log created successfully"}

@router.post("/rules/update_and_push")
def update_rules_and_push():
    return update_rules_and_push