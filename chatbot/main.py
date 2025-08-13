from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import configuration
from config.settings import ALLOWED_ORIGINS

# Import database setup
from database import engine, get_db
import models
from models import User, ChatSession, Message
import schemas

# Import API routes
from api.auth_routes import router as auth_router
from api.chat_routes import router as chat_router
from api.document_routes import router as document_router
from api.admin_routes import router as admin_router

# Import dependencies
from dependencies import get_current_user

# Import rate limiting for status endpoint
from rate_limiting.rate_limiter import get_client_ip, rate_limit_storage
import crud

# Initialize database
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="ChatBot API",
    description="Clean AI-powered chatbot with authentication",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(document_router)
app.include_router(admin_router)

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "ChatBot API is running!",
        "version": "2.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ChatBot API"}

@app.get("/test/db")
async def test_database(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Test database connection and user access"""
    try:
        # Test basic database query
        user_count = db.query(User).count()
        session_count = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).count()
        
        return {
            "status": "success",
            "user_id": current_user.id,
            "total_users": user_count,
            "user_sessions": session_count
        }
    except Exception as e:
        print(f"Database test error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/chat/history", response_model=schemas.ChatHistoryListResponse)
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

@app.get("/chat/history/{session_id}")
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

@app.delete("/chat/history/{session_id}")
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

@app.delete("/chat/history")
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

@app.put("/chat/history/{session_id}/title")
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

# ============================================================================
# RATE LIMIT STATUS ENDPOINT
# ============================================================================

@app.get("/rate-limit/status")
async def get_rate_limit_status(request: Request):
    """Get current rate limit status for the requesting IP"""
    client_ip = get_client_ip(request)
    ip_data = rate_limit_storage.get(client_ip, {'requests': 0, 'files': 0, 'reset_time': 0})
    
    from config.settings import MAX_REQUESTS_PER_IP, MAX_FILES_PER_IP
    
    return {
        "requests": ip_data['requests'],
        "files": ip_data['files'],
        "maxRequests": MAX_REQUESTS_PER_IP,
        "maxFiles": MAX_FILES_PER_IP,
        "resetTime": ip_data['reset_time']
    }

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ChatBot API Server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
