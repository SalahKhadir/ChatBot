from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import User, ChatSession, Message
from schemas import UserCreate, ChatSessionCreate, MessageCreate
from auth import get_password_hash, verify_password
from typing import Optional, List
import json

# User CRUD operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# Chat session CRUD operations
def create_chat_session(db: Session, session_id: str, user_id: int, title: Optional[str] = None) -> ChatSession:
    db_session = ChatSession(
        session_id=session_id,
        user_id=user_id,
        title=title
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_chat_session(db: Session, session_id: str) -> Optional[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

def get_user_chat_sessions(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(desc(ChatSession.updated_at)).offset(skip).limit(limit).all()

def update_chat_session_document_context(db: Session, session_id: str, has_documents: bool, document_info: dict = None):
    db_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if db_session:
        db_session.has_document_context = has_documents
        if document_info:
            db_session.document_info = json.dumps(document_info)
        db.commit()
        db.refresh(db_session)
    return db_session

# Message CRUD operations
def create_message(db: Session, message: MessageCreate, user_id: int, session_id: int, has_document_context: bool = False) -> Message:
    db_message = Message(
        user_id=user_id,
        session_id=session_id,
        message_type=message.message_type,
        content=message.content,
        has_document_context=has_document_context
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_session_messages(db: Session, session_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
    return db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).offset(skip).limit(limit).all()

def get_user_messages(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
    return db.query(Message).filter(Message.user_id == user_id).order_by(desc(Message.created_at)).offset(skip).limit(limit).all()
