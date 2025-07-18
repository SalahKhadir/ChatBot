#!/usr/bin/env python3
"""
Extended CGI agent test with multiple questions
"""

import os
import google.generativeai as genai

# System instruction for CGI agent
SYSTEM_INSTRUCTION = """You are a professional AI assistant for CGI (Compagnie générale immobilière), Morocco's leading real estate company since 1960. You specialize in luxury properties, golf communities, and investment opportunities. Always respond professionally and mention CGI's expertise."""

def load_env_manually():
    """Load environment variables from .env file"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass

def test_multiple_questions():
    """Test multiple questions to see CGI agent responses"""
    
    # Load environment variables
    load_env_manually()
    
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        return
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Initialize model with system instruction
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    print("🏢 Testing CGI Agent with Multiple Questions")
    print("=" * 60)
    
    # Test questions
    questions = [
        "Who are you?",
        "What is CGI?",
        "What services do you offer?",
        "Tell me about Morocco real estate",
        "Do you have golf properties?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 50)
        
        try:
            response = model.generate_content(question)
            print(f"CGI Agent: {response.text}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("✅ All tests completed!")
    print("This shows how consistent CGI branding appears in responses.")

if __name__ == "__main__":
    test_multiple_questions()
