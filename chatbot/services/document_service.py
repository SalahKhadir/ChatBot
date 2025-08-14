from typing import List
import uuid
from fastapi import UploadFile, HTTPException
from google import genai
from google.genai import types
from services.ai_service import gemini_client, document_sessions
from config.settings import CGI_SYSTEM_INSTRUCTION, CGI_CV_ANALYSIS_INSTRUCTION

async def process_uploaded_files(files: List[UploadFile]) -> tuple:
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

async def analyze_documents_with_ai(file_contents: list, prompt: str, file_count: int) -> str:
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
    # Determine if this is CV analysis by checking file content or prompt keywords
    is_cv_analysis = any(keyword in prompt.lower() for keyword in 
                        ['cv', 'resume', 'candidate', 'skills', 'experience', 'qualifications', 'hire', 'recruit'])
    
    # Use specialized instruction for CV analysis
    system_instruction = CGI_CV_ANALYSIS_INSTRUCTION if is_cv_analysis else CGI_SYSTEM_INSTRUCTION
    
    gemini_contents.append(
        f"Based on the {file_count} PDF document(s) provided above, please answer the following question: {prompt}"
    )

    # Generate response
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=gemini_contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    )

    return response.text

def create_document_session(file_contents: list, file_info: list, prompt: str, response_text: str, user_id=None) -> str:
    """Create a new document session and return session ID"""
    session_id = str(uuid.uuid4())
    document_sessions[session_id] = {
        'file_contents': file_contents,
        'file_info': file_info,
        'conversation_history': [f"User: {prompt}", f"Assistant: {response_text}"],
        'user_id': user_id
    }
    return session_id
