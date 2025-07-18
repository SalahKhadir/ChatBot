import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from typing import Optional, List
import uuid
from sqlalchemy.orm import Session

# Import authentication and database modules
from database import get_db, engine
from models import User
from schemas import UserCreate, UserLogin, UserResponse, Token
from auth import verify_password, get_password_hash, create_access_token
from crud import get_user_by_email, create_user, get_user
from dependencies import get_current_user
import models

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY environment variable is required")

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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Gemini client
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✓ Gemini AI client initialized successfully")
except Exception as e:
    raise Exception(f"Failed to initialize Gemini client: {e}")

# CGI System Instruction
CGI_SYSTEM_INSTRUCTION = """You are a professional AI assistant for CGI (Compagnie générale immobilière), Morocco's leading real estate company since 1960. You specialize in luxury properties, golf communities, and investment opportunities. Always respond professionally and mention CGI's expertise."""

# In-memory storage for document sessions
document_sessions = {}

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
    return {
        "status": "healthy",
        "gemini_client": "connected",
        "database": "connected"
    }

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        print(f"🔍 Registration attempt for email: {user.email}")
        
        # Check if user already exists
        existing_user = get_user_by_email(db, user.email)
        if existing_user:
            print(f"❌ Email {user.email} already exists")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        db_user = create_user(db, user)
        print(f"✅ User created successfully: {db_user.email}")
        
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login", response_model=Token)
async def login_user(user: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    try:
        print(f"🔍 Login attempt for email: {user.email}")
        
        # Verify user credentials
        db_user = get_user_by_email(db, user.email)
        if not db_user:
            print(f"❌ User not found: {user.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not verify_password(user.password, db_user.hashed_password):
            print(f"❌ Invalid password for user: {user.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token = create_access_token(data={"sub": str(db_user.id)})
        print(f"✅ Login successful for user: {db_user.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=db_user.id,
                email=db_user.email,
                full_name=db_user.full_name,
                is_active=db_user.is_active,
                created_at=db_user.created_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/debug-token")
async def debug_token(authorization: str = None):
    """Debug endpoint to check token structure"""
    if not authorization:
        return {"error": "No authorization header provided"}
    
    try:
        # Extract token from Bearer header
        token = authorization.replace("Bearer ", "")
        
        # Import jwt for debugging
        from jose import jwt
        
        # Get SECRET_KEY from environment
        SECRET_KEY = os.getenv("SECRET_KEY", "whatisasecretkeyJWT")
        
        # Try to decode
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"decoded_payload": payload}
    except Exception as e:
        return {"error": str(e)}

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@app.post("/chat")
async def chat_with_ai(
    message: str = Form(...), 
    session_id: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Chat with AI (authenticated users only)"""
    try:
        # Check if there's a document session for context
        if session_id and session_id in document_sessions:
            response_text = await _chat_with_document_context(message, session_id)
            return {
                "response": response_text,
                "session_id": session_id,
                "has_document_context": True,
                "user": current_user.full_name
            }
        else:
            # Regular chat without document context
            response_text = await _chat_without_context(message)
            return {
                "response": response_text,
                "user": current_user.full_name
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-document")
async def analyze_documents(
    files: List[UploadFile] = File(...),
    prompt: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Analyze PDF documents with AI (authenticated users only)"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Validate and process files
        file_contents, file_info = await _process_uploaded_files(files)
        
        # Generate AI response
        response_text = await _analyze_documents_with_ai(file_contents, prompt, len(files))
        
        # Store session for follow-up questions
        session_id = str(uuid.uuid4())
        document_sessions[session_id] = {
            'file_contents': file_contents,
            'file_info': file_info,
            'conversation_history': [f"User: {prompt}", f"Assistant: {response_text}"],
            'user_id': current_user.id
        }

        return {
            "response": response_text,
            "files_processed": file_info,
            "total_files": len(files),
            "session_id": session_id,
            "user": current_user.full_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PUBLIC ENDPOINTS (No Authentication Required)
# ============================================================================

@app.post("/chat/public")
async def chat_public(message: str = Form(...), session_id: str = Form(None)):
    """Chat with AI (public access)"""
    try:
        # Check if there's a document session for context
        if session_id and session_id in document_sessions:
            response_text = await _chat_with_document_context(message, session_id)
            return {
                "response": response_text,
                "session_id": session_id,
                "has_document_context": True
            }
        else:
            # Regular chat without document context
            response_text = await _chat_without_context(message)
            return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-document/public")
async def analyze_documents_public(
    files: List[UploadFile] = File(...),
    prompt: str = Form(...)
):
    """Analyze PDF documents with AI (public access)"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Validate and process files
        file_contents, file_info = await _process_uploaded_files(files)
        
        # Generate AI response
        response_text = await _analyze_documents_with_ai(file_contents, prompt, len(files))
        
        # Store session for follow-up questions
        session_id = str(uuid.uuid4())
        document_sessions[session_id] = {
            'file_contents': file_contents,
            'file_info': file_info,
            'conversation_history': [f"User: {prompt}", f"Assistant: {response_text}"],
            'user_id': None  # Public access
        }

        return {
            "response": response_text,
            "files_processed": file_info,
            "total_files": len(files),
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _chat_without_context(message: str) -> str:
    """Generate AI response without document context using CGI system instruction"""
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[message],
        config=types.GenerateContentConfig(
            system_instruction=CGI_SYSTEM_INSTRUCTION
        )
    )
    return response.text

async def _chat_with_document_context(message: str, session_id: str) -> str:
    """Generate AI response with document context"""
    session_data = document_sessions[session_id]
    
    # Build context with documents and conversation history
    gemini_contents = []
    
    # Add all PDF files from the session
    for file_content in session_data['file_contents']:
        gemini_contents.append(
            types.Part.from_bytes(
                data=file_content,
                mime_type='application/pdf',
            )
        )
    
    # Add conversation history
    for msg in session_data['conversation_history']:
        gemini_contents.append(msg)
    
    # Add current message
    gemini_contents.append(f"User: {message}")
    
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=gemini_contents,
        config=types.GenerateContentConfig(
            system_instruction=CGI_SYSTEM_INSTRUCTION
        )
    )
    
    # Update conversation history
    session_data['conversation_history'].append(f"User: {message}")
    session_data['conversation_history'].append(f"Assistant: {response.text}")
    
    return response.text

async def _process_uploaded_files(files: List[UploadFile]) -> tuple:
    """Process and validate uploaded PDF files"""
    file_contents = []
    file_info = []
    
    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} is not a PDF. Only PDF files are supported"
            )
        
        file_content = await file.read()
        file_contents.append(file_content)
        file_info.append({
            "filename": file.filename,
            "size": len(file_content)
        })
    
    return file_contents, file_info

async def _analyze_documents_with_ai(file_contents: list, prompt: str, file_count: int) -> str:
    """Analyze documents using AI"""
    # Prepare content for Gemini
    gemini_contents = []
    
    # Add all PDF files
    for file_content in file_contents:
        gemini_contents.append(
            types.Part.from_bytes(
                data=file_content,
                mime_type='application/pdf',
            )
        )
    
    # Add the prompt
    gemini_contents.append(
        f"Based on the {file_count} PDF document(s) provided above, please answer the following question: {prompt}"
    )

    # Generate response
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=gemini_contents,
        config=types.GenerateContentConfig(
            system_instruction=CGI_SYSTEM_INSTRUCTION
        )
    )

    return response.text

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ChatBot API Server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
