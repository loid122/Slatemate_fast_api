from fastapi import APIRouter, Depends
from app.control.schemas import Rule, Log  # (define these in schemas.py)
from app.control.services import (
    login_user,
    get_rules,
    get_logs,
    update_and_push_rules
)

router = APIRouter()

@router.post("/login")
def login(username: str, password: str):
    return login_user(username, password)

@router.get("/rules", response_model=list[Rule])
def rules():
    return get_rules()

@router.get("/logs", response_model=list[Log])
def logs():
    return get_logs()

@router.post("/rules/update_and_push")
def update_rules_and_push():
    return update_and_push_rules()
