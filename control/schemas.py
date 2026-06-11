from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access: str
    refresh: str

class RuleRequest(BaseModel):
    websites: List[str]
    words: List[str]
    categories: List[str]

class RuleResponse(BaseModel):
    websites: List[str]
    words: List[str]
    categories: List[str]
    allowed_list: List[str]

class LogRequest(BaseModel):
    url: str

class MessageResponse(BaseModel):
    message: str
