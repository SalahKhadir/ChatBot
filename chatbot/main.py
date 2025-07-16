import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
import pathlib
import tempfile
from typing import Optional

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

@app.post("/chat")
async def chat(message: str = Form(...)):
    """Handle simple text-based chat messages"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[message]
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-document")
async def analyze_document(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    """Handle document analysis with PDF/document upload"""
    try:
        # Check if file is a PDF
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read the file content
        file_content = await file.read()
        
        # Generate response using Gemini with PDF content
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                types.Part.from_bytes(
                    data=file_content,
                    mime_type='application/pdf',
                ),
                prompt
            ]
        )
        
        return {
            "response": response.text,
            "filename": file.filename,
            "file_size": len(file_content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

