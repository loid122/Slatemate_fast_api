# app/routers/logs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db  # <<<<<< Use this import
from .. import schemas, models
from ..auth_utils import get_current_user

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.post("/", response_model=schemas.MessageResponse)
def create_log(data: schemas.LogRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not data.url:
        raise HTTPException(status_code=400, detail="URL is required")

    log = models.Log(user_id=current_user.id, url=data.url[:2048])
    db.add(log)
    db.commit()
    return {"message": "Log created successfully"}
