# app/control/services/rules.py

from sqlalchemy.orm import Session
from app.control import models
from app.db.session import get_db
from app.control.models import Category, Website


def clear_allowed_list(db: Session, user):
    rule = db.query(models.Rule).filter_by(user_id=user.id).first()
    if rule:
        rule.allowed_list = []
        db.commit()


def add_to_allowed_list(db: Session, user, domain):
    rule = db.query(models.Rule).filter_by(user_id=user.id).first()
    if rule:
        allowed = set(rule.allowed_list or [])
        allowed.add(domain)
        rule.allowed_list = list(allowed)
        db.commit()


def get_user_rule(db: Session, user):
    rule = db.query(models.Rule).filter_by(user_id=user.id).first()
    if rule:
        return {
            "blocked_words": rule.words,
            "blocked_websites": rule.websites,
            "allowed_websites": rule.allowed_list or []
        }
    return {"blocked_words": [], "blocked_websites": [], "allowed_websites": []}


def log_blocked_url(db: Session, user, url):
    log = models.Log(user_id=user.id, url=url[:2048])
    db.add(log)
    db.commit()


def get_category_from_db(db: Session, domain: str):
    """
    ORM version: Get category name for a given domain.
    """
    result = (
        db.query(Category.category_name)
        .join(Website, Website.category_id == Category.id)
        .filter(Website.website_name.ilike(domain))  # case-insensitive match
        .first()
    )
    return result[0] if result else None
