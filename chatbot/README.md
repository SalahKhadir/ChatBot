# ChatBot API v2.0 - Clean & Simple

A clean, well-organized AI-powered chatbot API using FastAPI and Google Gemini AI with user authentication.

## 🚀 Features

- **Authentication System**: JWT-based user registration and login
- **AI Chat**: Powered by Google Gemini 2.0 Flash
- **Document Analysis**: Upload and analyze multiple PDF files
- **Session Management**: Persistent context for follow-up questions
- **Public API**: Some endpoints available without authentication
- **Clean Architecture**: Well-organized, readable code

## 📁 Project Structure

```
chatbot/
├── main.py              # Main FastAPI application (clean & organized)
├── database.py          # Database configuration
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic request/response schemas
├── auth.py              # JWT authentication utilities
├── crud.py              # Database operations
├── dependencies.py      # FastAPI dependencies
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
└── README.md           # This file
```

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file with:
```
GEMINI_API_KEY=your_google_gemini_api_key
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=chatbot
SECRET_KEY=your_secret_key_for_jwt
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### 3. Database Setup
```bash
python init_db.py
```

### 4. Run the Server
```bash
python main.py
```

The server will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs

## 🔗 API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Chat (Authenticated)
- `POST /chat` - Chat with AI
- `POST /analyze-document` - Analyze PDF documents

### Public Chat (No Auth Required)
- `POST /chat/public` - Public chat access

## 📝 Usage Examples

### Register a User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "password123"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Chat with AI
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "message=Hello, how are you?"
```

## 🧹 What's Been Cleaned

1. **Code Organization**: Clear sections with comments
2. **Function Separation**: Helper functions for reusability
3. **Error Handling**: Consistent error responses
4. **Documentation**: Clear docstrings for all endpoints
5. **Configuration**: Centralized environment variables
6. **Naming**: Descriptive variable and function names
7. **Structure**: Logical grouping of related functionality

## 🔧 Development

The backend is now much cleaner and easier to maintain:
- All endpoints are clearly organized
- Helper functions prevent code duplication
- Error handling is consistent
- Documentation is built-in
- Easy to extend and modify
