from google import genai
from google.genai import types
from typing import List
from fastapi import UploadFile, HTTPException
from config.settings import GEMINI_API_KEY, CGI_SYSTEM_INSTRUCTION, CGI_CREATIVE_WRITING_INSTRUCTION, CGI_CODE_DEVELOPMENT_INSTRUCTION, CGI_PROBLEM_SOLVING_INSTRUCTION

# Initialize Gemini client
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✓ Gemini AI client initialized successfully")
except Exception as e:
    raise Exception(f"Failed to initialize Gemini client: {e}")

# In-memory storage for document sessions
document_sessions = {}

async def chat_without_context(message: str) -> str:
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

async def chat_with_document_context(message: str, session_id: str) -> str:
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
