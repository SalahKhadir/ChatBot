import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
import pathlib
import tempfile
from typing import Optional, List
import uuid

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
KEY = os.getenv("GEMINI_API_KEY")

# Check if API key is available
if not KEY:
    print("ERROR: GEMINI_API_KEY environment variable is not set!")
    print("Please set your Gemini API key as an environment variable.")
    exit(1)

print(f"✓ API key loaded: {KEY[:5]}...")  # Show first 10 chars for verification

app = FastAPI()

# Add CORS middleware to allow requests from your React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the client after confirming API key is available
try:
    client = genai.Client(api_key=KEY)
    print("✓ Gemini client initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize Gemini client: {e}")
    exit(1)

# Store document sessions in memory (in production, use a database)
document_sessions = {}

@app.post("/chat")
async def chat(message: str = Form(...), session_id: str = Form(None)):
    """Handle simple text-based chat messages with optional document context"""
    try:
        # Check if there's a document session for this chat
        if session_id and session_id in document_sessions:
            # Continue conversation with document context
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
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=gemini_contents
            )
            
            # Update conversation history
            session_data['conversation_history'].append(f"User: {message}")
            session_data['conversation_history'].append(f"Assistant: {response.text}")
            
            return {
                "response": response.text,
                "session_id": session_id,
                "has_document_context": True
            }
        else:
            # Regular chat without document context
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[message]
            )
            return {"response": response.text}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-document")
async def analyze_document(
        files: List[UploadFile] = File(...),
        prompt: str = Form(...)
):
    """Handle document analysis with multiple PDF/document uploads"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Create a new session ID for this document analysis
        session_id = str(uuid.uuid4())
        
        # Process each file and collect content
        file_contents = []
        file_info = []
        
        for file in files:
            # Check if file is a PDF
            if file.content_type != "application/pdf":
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF. Only PDF files are supported")
            
            # Read the file content
            file_content = await file.read()
            file_contents.append(file_content)
            file_info.append({
                "filename": file.filename,
                "size": len(file_content)
            })
        
        # Prepare content for Gemini - include all PDFs and the prompt
        gemini_contents = []
        
        # Add all PDF files as parts
        for i, file_content in enumerate(file_contents):
            gemini_contents.append(
                types.Part.from_bytes(
                    data=file_content,
                    mime_type='application/pdf',
                )
            )
        
        # Add the user's prompt at the end
        gemini_contents.append(
            f"Based on the {len(files)} PDF document(s) provided above, please answer the following question or complete the following task: {prompt}"
        )

        # Generate response using Gemini with all PDF contents
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=gemini_contents
        )

        # Store the session data for future context
        document_sessions[session_id] = {
            'file_contents': file_contents,
            'file_info': file_info,
            'conversation_history': [
                f"User: {prompt}",
                f"Assistant: {response.text}"
            ]
        }

        return {
            "response": response.text,
            "files_processed": file_info,
            "total_files": len(files),
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
