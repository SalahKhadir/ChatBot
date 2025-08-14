from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# User role enum
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

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
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserManagement(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    total_sessions: Optional[int] = 0
    total_messages: Optional[int] = 0
    
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

# Chat History schemas
class ChatHistoryResponse(BaseModel):
    id: int
    session_id: str
    title: Optional[str]
    preview: str
    message_count: int
    has_document_context: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ChatHistoryListResponse(BaseModel):
    chat_sessions: List[ChatHistoryResponse]
    total_count: int

class ChatSessionWithMessages(BaseModel):
    id: int
    session_id: str
    title: Optional[str]
    has_document_context: bool
    created_at: datetime
    messages: List[MessageResponse]
    
    class Config:
        from_attributes = True
