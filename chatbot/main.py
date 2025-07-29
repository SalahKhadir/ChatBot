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
from models import User, ChatSession, Message
from schemas import UserCreate, UserLogin, UserResponse, Token, MessageCreate
import schemas
from auth import verify_password, get_password_hash, create_access_token
from crud import get_user_by_email, create_user, get_user
import crud
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

# CGI System Instructions for different sections
CGI_SYSTEM_INSTRUCTION = """You are a professional AI assistant for CGI (Compagnie générale immobilière), Morocco's leading real estate company since 1960. You specialize in luxury properties, golf communities, and investment opportunities. Always respond professionally and mention CGI's expertise."""

CGI_CREATIVE_WRITING_INSTRUCTION = """You are a creative writing specialist for CGI Real Estate. Help create compelling property descriptions, marketing copy, blog posts, and creative content related to luxury real estate, golf communities, and Moroccan properties. Focus on elegant, persuasive language that highlights CGI's premium offerings and 60+ years of expertise."""

CGI_CODE_DEVELOPMENT_INSTRUCTION = """You are a senior software developer and code reviewer specializing in real estate technology solutions. Help with code analysis, debugging, API development, database design, and web development. Provide practical solutions for real estate applications, property management systems, and modern web technologies."""

CGI_PROBLEM_SOLVING_INSTRUCTION = """You are a strategic consultant and problem-solving expert for CGI Real Estate. Break down complex business problems, provide step-by-step analysis, offer multiple solution approaches, and help with decision-making processes. Focus on real estate market analysis, investment strategies, and business optimization."""

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

@app.get("/debug/stats")
async def debug_stats(db: Session = Depends(get_db)):
    """Debug endpoint to check database stats (no auth required)"""
    try:
        total_users = db.query(User).count()
        total_sessions = db.query(ChatSession).count()
        total_messages = db.query(Message).count()
        
        # Get recent sessions
        recent_sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).limit(5).all()
        
        return {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "recent_sessions": [
                {
                    "id": s.session_id,
                    "title": s.title,
                    "user_id": s.user_id,
                    "created_at": s.created_at.isoformat()
                } for s in recent_sessions
            ]
        }
    except Exception as e:
        print(f"Debug stats error: {e}")
        return {"error": str(e)}

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
            response_text = await _chat_with_document_context(message, session_id)
            has_document_context = True
        else:
            # Regular chat without document context
            response_text = await _chat_without_context(message)
        
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
            "has_document_context": has_document_context,
            "user": current_user.full_name
        }
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-document")
async def analyze_documents(
    files: List[UploadFile] = File(...),
    prompt: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze PDF documents with AI (authenticated users only)"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Validate and process files
        file_contents, file_info = await _process_uploaded_files(files)
        
        # Generate AI response
        response_text = await _analyze_documents_with_ai(file_contents, prompt, len(files))
        
        # Create new session for document analysis
        session_id = str(uuid.uuid4())
        db_session = crud.create_chat_session(db, session_id, current_user.id)
        
        # Update session with document context
        document_info = {"files": file_info, "total_files": len(files)}
        crud.update_chat_session_document_context(db, session_id, True, document_info)
        
        # Save user message (prompt) to database
        user_message = MessageCreate(content=prompt, message_type="user")
        crud.create_message(db, user_message, current_user.id, db_session.id, True)
        
        # Save AI response to database
        ai_message = MessageCreate(content=response_text, message_type="ai")
        crud.create_message(db, ai_message, current_user.id, db_session.id, True)
        
        # Set session title based on first user message
        title = prompt[:50] + "..." if len(prompt) > 50 else prompt
        crud.update_chat_session_title(db, session_id, current_user.id, title)
        
        # Store session for follow-up questions (in-memory for backward compatibility)
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
        print(f"Document analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
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

@app.post("/analyze-secure-folder")
async def analyze_secure_folder(
    prompt: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze CVs from secure folder (authenticated users only)"""
    try:
        # Define the secure folder path (you can configure this as an environment variable)
        SECURE_FOLDER_PATH = os.getenv("SECURE_CV_FOLDER_PATH", "C:/secure/cvs")
        
        if not os.path.exists(SECURE_FOLDER_PATH):
            raise HTTPException(status_code=404, detail="Secure folder not found")
        
        # Get all PDF files from the secure folder
        pdf_files = []
        for filename in os.listdir(SECURE_FOLDER_PATH):
            if filename.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(SECURE_FOLDER_PATH, filename))
        
        if not pdf_files:
            raise HTTPException(status_code=404, detail="No PDF files found in secure folder")
        
        # Read and process the PDF files
        file_contents = []
        file_info = []
        
        for file_path in pdf_files:
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    file_contents.append(file_content)
                    file_info.append({
                        "filename": os.path.basename(file_path),
                        "size": len(file_content)
                    })
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue
        
        if not file_contents:
            raise HTTPException(status_code=500, detail="Failed to read any files from secure folder")
        
        # Generate AI response with CV analysis focus
        cv_analysis_prompt = f"""
        You are analyzing CVs from a confidential recruitment process. Please provide:
        
        User Request: {prompt}
        
        Guidelines for CV Analysis:
        - Maintain confidentiality and professionalism
        - Focus on relevant skills, experience, and qualifications
        - Provide comparative analysis when requested
        - Respect privacy by not revealing personal details unless specifically asked
        - Summarize key findings and recommendations
        
        Please analyze the CVs and respond to the user's request.
        """
        
        response_text = await _analyze_documents_with_ai(file_contents, cv_analysis_prompt, len(file_contents))
        
        # Create new session for document analysis
        session_id = str(uuid.uuid4())
        db_session = crud.create_chat_session(db, session_id, current_user.id)
        
        # Update session with document context
        document_info = {"files": file_info, "total_files": len(file_contents), "source": "secure_folder"}
        crud.update_chat_session_document_context(db, session_id, True, document_info)
        
        # Save user message (prompt) to database
        user_message = MessageCreate(content=prompt, message_type="user")
        crud.create_message(db, user_message, current_user.id, db_session.id, True)
        
        # Save AI response to database
        ai_message = MessageCreate(content=response_text, message_type="ai")
        crud.create_message(db, ai_message, current_user.id, db_session.id, True)
        
        # Set session title based on first user message
        title = f"CV Analysis: {prompt[:30]}..." if len(prompt) > 30 else f"CV Analysis: {prompt}"
        crud.update_chat_session_title(db, session_id, current_user.id, title)
        
        # Store session for follow-up questions (in-memory for backward compatibility)
        document_sessions[session_id] = {
            'file_contents': file_contents,
            'file_info': file_info,
            'conversation_history': [f"User: {prompt}", f"Assistant: {response_text}"],
            'user_id': current_user.id,
            'source': 'secure_folder'
        }

        return {
            "response": response_text,
            "files_processed": file_info,
            "total_files": len(file_contents),
            "session_id": session_id,
            "source": "secure_folder"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in secure folder analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _chat_without_context(message: str) -> str:
    """Generate AI response without document context using appropriate system instruction"""
    
    # Detect the type of request based on message content
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['creative writing', 'content', 'story', 'essay', 'blog', 'marketing', 'property description']):
        system_instruction = CGI_CREATIVE_WRITING_INSTRUCTION
    elif any(keyword in message_lower for keyword in ['code', 'programming', 'development', 'debug', 'api', 'database', 'script']):
        system_instruction = CGI_CODE_DEVELOPMENT_INSTRUCTION
    elif any(keyword in message_lower for keyword in ['problem', 'solving', 'solution', 'analysis', 'strategy', 'decision', 'step by step']):
        system_instruction = CGI_PROBLEM_SOLVING_INSTRUCTION
    else:
        system_instruction = CGI_SYSTEM_INSTRUCTION
    
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[message],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
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
# CHAT HISTORY ENDPOINTS
# ============================================================================

@app.get("/chat/history", response_model=schemas.ChatHistoryListResponse)
async def get_chat_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat history"""
    try:
        # Use simpler query to avoid SQL issues
        chat_sessions = crud.get_user_chat_sessions(db, current_user.id, skip, limit)
        
        history_items = []
        for session in chat_sessions:
            # Get message count for this session
            message_count = db.query(Message).filter(Message.session_id == session.id).count()
            
            # Get first message for preview
            first_message = db.query(Message).filter(
                Message.session_id == session.id,
                Message.message_type == "user"
            ).order_by(Message.created_at).first()
            
            preview = "No messages"
            if first_message:
                preview = first_message.content[:100] + "..." if len(first_message.content) > 100 else first_message.content
            
            history_items.append(schemas.ChatHistoryResponse(
                id=session.id,
                session_id=session.session_id,
                title=session.title or f"Chat {session.created_at.strftime('%m/%d/%Y')}",
                preview=preview,
                message_count=message_count,
                has_document_context=session.has_document_context,
                created_at=session.created_at,
                updated_at=session.updated_at
            ))
        
        return schemas.ChatHistoryListResponse(
            chat_sessions=history_items,
            total_count=len(history_items)
        )
        
    except Exception as e:
        print(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

@app.get("/chat/history/{session_id}", response_model=schemas.ChatSessionWithMessages)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session with all messages"""
    try:
        chat_session = crud.get_chat_session_with_messages(db, session_id, current_user.id)
        
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        messages = crud.get_session_messages(db, chat_session.id)
        
        message_responses = [
            schemas.MessageResponse(
                id=msg.id,
                message_type=msg.message_type,
                content=msg.content,
                has_document_context=msg.has_document_context,
                created_at=msg.created_at
            ) for msg in messages
        ]
        
        return schemas.ChatSessionWithMessages(
            id=chat_session.id,
            session_id=chat_session.session_id,
            title=chat_session.title,
            has_document_context=chat_session.has_document_context,
            created_at=chat_session.created_at,
            messages=message_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat session")

@app.delete("/chat/history/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific chat session"""
    try:
        success = crud.delete_chat_session(db, session_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {"message": "Chat session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat session")

@app.delete("/chat/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all chat history for the current user"""
    try:
        success = crud.clear_user_chat_history(db, current_user.id)
        
        return {"message": f"Chat history cleared successfully. Removed sessions: {success}"}
        
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear chat history")

@app.put("/chat/history/{session_id}/title")
async def update_chat_title(
    session_id: str,
    title: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the title of a chat session"""
    try:
        updated_session = crud.update_chat_session_title(db, session_id, current_user.id, title)
        
        if not updated_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {"message": "Chat title updated successfully", "title": title}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating chat title: {e}")
        raise HTTPException(status_code=500, detail="Failed to update chat title")

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ChatBot API Server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
