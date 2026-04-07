from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class User(BaseModel):
    username: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Message(BaseModel):
    sender: str
    receiver: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    emotion: Optional[str] = None
    trust_score: Optional[float] = None
    is_sarcasm: Optional[bool] = None
