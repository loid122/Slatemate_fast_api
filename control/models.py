from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


def default_list():
    return []



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Relationships
    rule = relationship("Rule", back_populates="user", uselist=False, cascade="all, delete-orphan")

    logs = relationship("Log", back_populates="user")



# Rule model

class Rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    words = Column(JSON, default=default_list)
    websites = Column(JSON, default=default_list)
    categories = Column(JSON, default=default_list)
    allowed_list = Column(JSON, default=default_list)

    user = relationship("User", back_populates="rule")


# Log model
class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    url = Column(String(2048))
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")
