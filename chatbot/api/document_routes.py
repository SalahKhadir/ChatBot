from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import uuid
import models

from database import get_db
from models import User
from schemas import MessageCreate
from dependencies import get_current_user, get_current_admin
from services.document_service import process_uploaded_files, analyze_documents_with_ai, create_document_session
from services.ai_service import document_sessions
from rate_limiting.rate_limiter import check_rate_limit, increment_rate_limit
import crud

router = APIRouter()

@router.post("/analyze-document")
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
        file_contents, file_info = await process_uploaded_files(files)
        
        # Generate AI response
        response_text = await analyze_documents_with_ai(file_contents, prompt, len(files))
        
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

@router.post("/analyze-document/public")
async def analyze_documents_public(
    request: Request,
    files: List[UploadFile] = File(...),
    prompt: str = Form(...)
):
    """Analyze PDF documents with AI (public access) - Rate limited"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Check file upload rate limit for non-authenticated users
        file_rate_check = check_rate_limit(request, "file")
        if not file_rate_check["allowed"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "File upload limit exceeded",
                    "message": file_rate_check["message"],
                    "type": "file_limit",
                    "requires_login": True
                }
            )
        
        # Check general request rate limit
        request_rate_check = check_rate_limit(request, "request")
        if not request_rate_check["allowed"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": request_rate_check["message"],
                    "type": "rate_limit",
                    "requires_login": True
                }
            )
        
        # Validate and process files
        file_contents, file_info = await process_uploaded_files(files)
        
        # Generate AI response
        response_text = await analyze_documents_with_ai(file_contents, prompt, len(files))
        
        # Increment counters after successful operation
        increment_rate_limit(request, "request")
        increment_rate_limit(request, "file")
        
        # Create document session
        session_id = create_document_session(file_contents, file_info, prompt, response_text, None)

        return {
            "response": response_text,
            "files_processed": file_info,
            "total_files": len(files),
            "session_id": session_id,
            "rate_limit": {
                "remaining_requests": request_rate_check["remaining"] - 1,  # -1 because we just used one
                "remaining_files": file_rate_check["remaining"] - 1,  # -1 because we just used one
                "message": f"Upload successful! {file_rate_check['remaining'] - 1} file uploads remaining before sign-in required."
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-secure-folder")
async def analyze_secure_folder(
    prompt: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze CVs from secure folder (authenticated users with permission only)"""
    import os
    try:
        # Admins have automatic access, regular users need permission
        if current_user.role != "admin":
            permission = db.query(models.SecureFolderPermission).filter(
                models.SecureFolderPermission.user_id == current_user.id,
                models.SecureFolderPermission.has_access == True
            ).first()
            
            if not permission:
                raise HTTPException(
                    status_code=403, 
                    detail="Access denied. You don't have permission to analyze CVs from the secure folder. Please contact an administrator for access or upload your own documents to analyze."
                )
        
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
            raise HTTPException(
                status_code=404, 
                detail="No PDF files found in secure folder. Please contact an administrator to upload CV files."
            )
        
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
        
        response_text = await analyze_documents_with_ai(file_contents, cv_analysis_prompt, len(file_contents))
        
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
