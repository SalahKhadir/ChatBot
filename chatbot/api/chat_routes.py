from fastapi import APIRouter, Form, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from database import get_db
from models import User
from schemas import MessageCreate
from dependencies import get_current_user
from services.ai_service import chat_with_document_context, chat_without_context, document_sessions
from rate_limiting.rate_limiter import check_rate_limit, increment_rate_limit
import crud

router = APIRouter()

@router.post("/chat")
async def chat_with_ai(
    message: str = Form(...), 
    session_id: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with AI (authenticated users only)"""
    try:
        print(f"🔍 Chat request - User: {current_user.id}, Message: {message[:50]}...")
        
        # Get or create chat session
        if session_id:
            db_session = crud.get_chat_session(db, session_id)
            if not db_session or db_session.user_id != current_user.id:
                # Create new session if not found or doesn't belong to user
                session_id = str(uuid.uuid4())
                print(f"📝 Creating new session (existing invalid): {session_id}")
                db_session = crud.create_chat_session(db, session_id, current_user.id)
        else:
            # Create new session
            session_id = str(uuid.uuid4())
            print(f"📝 Creating new session: {session_id}")
            db_session = crud.create_chat_session(db, session_id, current_user.id)
        
        print(f"✅ Session created/found: {db_session.session_id}")
        
        # Save user message to database
        user_message = MessageCreate(content=message, message_type="user")
        print(f"💾 Saving user message to DB...")
        user_msg_db = crud.create_message(db, user_message, current_user.id, db_session.id, False)
        print(f"✅ User message saved with ID: {user_msg_db.id}")
        
        # Check if there's a document session for context
        has_document_context = False
        if session_id and session_id in document_sessions:
            response_text = await chat_with_document_context(message, session_id)
            has_document_context = True
        else:
            # Regular chat without document context
            response_text = await chat_without_context(message)
        
        print(f"🤖 AI response generated: {response_text[:50]}...")
        
        # Save AI response to database
        ai_message = MessageCreate(content=response_text, message_type="ai")
        print(f"💾 Saving AI response to DB...")
        ai_msg_db = crud.create_message(db, ai_message, current_user.id, db_session.id, has_document_context)
        print(f"✅ AI message saved with ID: {ai_msg_db.id}")
        
        # Update session title if it's the first message
        if not db_session.title:
            title = message[:50] + "..." if len(message) > 50 else message
            print(f"📝 Updating session title: {title}")
            crud.update_chat_session_title(db, session_id, current_user.id, title)
        
        print(f"🎉 Chat completed successfully")
        
        return {
            "response": response_text,
            "session_id": session_id,
            "has_document_context": has_document_context
        }
    
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/public")
async def chat_public(request: Request, message: str = Form(...), session_id: str = Form(None)):
    """Chat with AI (public access) - Rate limited"""
    try:
        # Check rate limit for non-authenticated users
        rate_check = check_rate_limit(request, "request")
        if not rate_check["allowed"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": rate_check["message"],
                    "type": "rate_limit",
                    "requires_login": True
                }
            )
        
        # Check if there's a document session for context
        if session_id and session_id in document_sessions:
            response_text = await chat_with_document_context(message, session_id)
            
            # Increment request counter after successful operation
            increment_rate_limit(request, "request")
            
            return {
                "response": response_text,
                "session_id": session_id,
                "has_document_context": True,
                "rate_limit": {
                    "remaining_requests": rate_check["remaining"] - 1,  # -1 because we just used one
                    "message": f"{rate_check['remaining'] - 1} requests remaining before sign-in required."
                }
            }
        else:
            # Regular chat without document context
            response_text = await chat_without_context(message)
            
            # Increment request counter after successful operation
            increment_rate_limit(request, "request")
            
            return {
                "response": response_text,
                "rate_limit": {
                    "remaining_requests": rate_check["remaining"] - 1,  # -1 because we just used one
                    "message": f"{rate_check['remaining'] - 1} requests remaining before sign-in required."
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
