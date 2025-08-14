from fastapi import APIRouter, Form, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from core.database import get_db
from core.models import User, ChatSession, Message
from core.schemas import MessageCreate
import core.schemas as schemas
from core.dependencies import get_current_user
from services.ai_service import chat_with_document_context, chat_without_context, document_sessions
from rate_limiting.rate_limiter import check_rate_limit, increment_rate_limit
import core.crud as crud

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

# ============================================================================
# CHAT HISTORY MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/chat/history", response_model=schemas.ChatHistoryListResponse)
async def get_chat_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat history"""
    try:
        sessions = crud.get_user_chat_sessions(db, current_user.id, skip, limit)
        total_count = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).count()
        
        # Transform sessions to ChatHistoryResponse format
        chat_sessions = []
        for session in sessions:
            # Get first message as preview
            first_message = db.query(Message).filter(
                Message.session_id == session.id
            ).order_by(Message.created_at).first()
            
            preview = first_message.content[:100] + "..." if first_message and len(first_message.content) > 100 else (first_message.content if first_message else "No messages")
            
            # Get message count
            message_count = db.query(Message).filter(Message.session_id == session.id).count()
            
            chat_sessions.append(schemas.ChatHistoryResponse(
                id=session.id,
                session_id=session.session_id,
                title=session.title or "New Chat",
                preview=preview,
                message_count=message_count,
                has_document_context=session.has_document_context or False,
                created_at=session.created_at,
                updated_at=session.updated_at
            ))
        
        return {"chat_sessions": chat_sessions, "total_count": total_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{session_id}")
async def get_chat_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a specific chat session"""
    try:
        messages = crud.get_chat_session_messages(db, session_id, current_user.id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/history/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific chat session"""
    try:
        success = crud.delete_chat_session(db, session_id, current_user.id)
        if success:
            return {"success": True, "message": "Chat session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Chat session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/history")
async def clear_all_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all chat history for the user"""
    try:
        success = crud.clear_user_chat_history(db, current_user.id)
        if success:
            return {"success": True, "message": "All chat history cleared successfully"}
        else:
            return {"success": True, "message": "No chat history to clear"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/chat/history/{session_id}/title")
async def update_chat_session_title(
    session_id: str,
    title: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update chat session title"""
    try:
        updated_session = crud.update_chat_session_title(db, session_id, current_user.id, title)
        if updated_session:
            return {"success": True, "message": "Title updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Chat session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
