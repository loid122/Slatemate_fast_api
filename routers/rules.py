from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, database, services
from ..auth_utils import get_current_user

router = APIRouter(prefix="/rules", tags=["Rules"])

@router.post("/", response_model=schemas.MessageResponse)
def update_rules(data: schemas.RuleRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    expanded_websites = services.expand_categories(data.categories, data.websites)

    rule = db.query(models.Rule).filter(models.Rule.user_id == current_user.id).first()
    if rule:
        rule.words = data.words
        rule.websites = expanded_websites
        rule.categories = data.categories
        rule.allowed_list = []
    else:
        rule = models.Rule(
            user_id=current_user.id,
            words=data.words,
            websites=expanded_websites,
            categories=data.categories,
            allowed_list=[]
        )
        db.add(rule)
    db.commit()

    # TODO: push via websocket here

    return schemas.MessageResponse(message="Rules updated and pushed successfully")

@router.get("/", response_model=schemas.RuleResponse)
def get_rules(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    rule = db.query(models.Rule).filter(models.Rule.user_id == current_user.id).first()
    if not rule:
        return {"websites": [], "words": [], "categories": [], "allowed_list": []}
    return {
        "websites": rule.websites,
        "words": rule.words,
        "categories": rule.categories,
        "allowed_list": rule.allowed_list
    }
