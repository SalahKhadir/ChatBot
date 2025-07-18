from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

# Chat session schemas
class ChatSessionCreate(BaseModel):
    title: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: int
    session_id: str
    title: Optional[str]
    has_document_context: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Message schemas
class MessageCreate(BaseModel):
    content: str
    message_type: str

class MessageResponse(BaseModel):
    id: int
    message_type: str
    content: str
    has_document_context: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Chat request schemas
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class DocumentAnalysisRequest(BaseModel):
    prompt: str
