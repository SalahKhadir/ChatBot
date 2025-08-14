from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import configuration
from config.settings import ALLOWED_ORIGINS

# Import database setup
from core.database import engine, get_db
import core.models as models
from core.models import User, ChatSession, Message
import core.schemas as schemas

# Import statistics middleware
# from core.statistics_middleware import StatisticsMiddleware

# Import API routes
from api.auth_routes import router as auth_router
from api.chat_routes import router as chat_router
from api.document_routes import router as document_router
from api.admin_routes import router as admin_router

# Import dependencies
from core.dependencies import get_current_user

# Import rate limiting for status endpoint
from rate_limiting.rate_limiter import get_client_ip, rate_limit_storage

# Initialize database
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="ChatBot API",
    description="Clean AI-powered chatbot with authentication",
    version="2.0.0"
)

# Add statistics middleware (before CORS) - temporarily disabled
# app.add_middleware(StatisticsMiddleware)

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
