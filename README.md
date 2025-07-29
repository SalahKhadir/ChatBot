# CGI Real Estate ChatBot 🏠🤖

An intelligent conversational AI assistant designed specifically for CGI (Compagnie générale immobilière), Morocco's leading real estate company. This full-stack application combines cutting-edge AI technology with robust user management and document analysis capabilities.

![ChatBot Demo](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688?style=flat&logo=fastapi)
![React](https://img.shields.io/badge/React-19.1.0-61DAFB?style=flat&logo=react)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python)

## 🌟 Features

### 🤖 AI-Powered Conversations
- **Google Gemini 2.0 Flash Integration**: Advanced AI responses with real estate expertise
- **Contextual Understanding**: Maintains conversation context for natural interactions
- **CGI-Specialized Responses**: Tailored for luxury properties, golf communities, and investment opportunities

### 📄 Document Analysis
- **PDF Document Processing**: Upload and analyze multiple PDF documents simultaneously
- **Intelligent Extraction**: AI-powered content analysis and question-answering
- **Document Context Preservation**: Maintains document context across conversation sessions
- **🔒 Secure CV Analysis**: Authenticated users can analyze CVs from protected secure folders
- **Dual Analysis Modes**: Public document upload vs. secure folder access for confidential files

### 👤 User Management & Authentication
- **JWT-Based Authentication**: Secure user login and registration system
- **Role-Based Access**: Different experience levels for authenticated vs. public users
- **User Profile Management**: Personalized experience with user data persistence

### 💾 Chat History Management
- **Persistent Chat Sessions**: Save and retrieve conversation history (authenticated users only)
- **ChatGPT-Style Interface**: Familiar sidebar navigation with chat history
- **Session Management**: Create, delete, and organize chat sessions
- **Real-time Updates**: Automatic refresh of chat history during conversations

### 🔒 Dual Access Modes
- **Public Access**: Basic chat functionality without data persistence
- **Authenticated Access**: Full feature set with history, document analysis, and data saving

### 🎨 Enhanced User Experience
- **Interactive Section Cards**: Visual toggle effects and hover animations for section selection
- **Active State Feedback**: Real-time visual indicators for selected sections with red accent theme
- **Conditional UI Elements**: Dynamic interface adaptation based on authentication status
- **Quick Start Prompts**: Context-aware prompt suggestions for each section (hidden for non-authenticated secure analysis)
- **Smooth Animations**: Polished transitions and micro-interactions throughout the interface

## � Latest Features & Improvements

### 🔐 Secure CV Analysis System
- **Protected Folder Access**: Authenticated users can analyze CVs from secure, protected folders
- **Environment-Configured Paths**: Secure folder location managed via `SECURE_CV_FOLDER_PATH` environment variable
- **Authentication-Gated**: Secure analysis features only available to logged-in users
- **Confidential Processing**: Specialized endpoint (`/analyze-secure-folder`) for sensitive document analysis

### 🎨 Enhanced Visual Experience
- **Section Toggle Effects**: Interactive cards with active state styling and hover-like animations
- **Red Accent Theme**: Consistent `#fb1b23` color scheme throughout the interface
- **Conditional Prompt Display**: Quick start prompts intelligently hidden for restricted features
- **Elevation Effects**: Cards lift and transform when selected for better user feedback
- **Theme Support**: Full light/dark mode compatibility for all new visual elements

### 🔄 Smart UI Adaptation
- **Authentication-Aware Interface**: UI elements automatically adapt based on login status
- **Contextual Feature Access**: Different capabilities shown to public vs. authenticated users
- **Progressive Enhancement**: Basic functionality for all users, premium features for authenticated accounts
- **Intelligent Fallbacks**: Graceful degradation when advanced features aren't available

## �🏗️ Architecture

### Backend (FastAPI)
```
chatbot/
├── main.py              # Main FastAPI application
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic data validation schemas
├── crud.py              # Database operations
├── auth.py              # Authentication utilities
├── dependencies.py      # FastAPI dependencies
├── database.py          # Database configuration
└── requirements.txt     # Python dependencies
```

### Frontend (React + Vite)
```
interface/
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── Navbar.jsx
│   │   ├── HistorySidebar.jsx
│   │   ├── Login.jsx
│   │   └── Signup.jsx
│   ├── pages/           # Main application pages
│   │   └── Home.jsx
│   ├── services/        # API communication
│   │   ├── api.js
│   │   └── chatHistoryService.js
│   ├── hooks/           # Custom React hooks
│   │   ├── useChatHistory.js
│   │   ├── useAutoScroll.js
│   │   └── useTypingAnimation.js
│   └── routes/          # Application routing
├── package.json
└── vite.config.js
```

## 🚀 Getting Started

### Prerequisites
- **Python 3.12+**
- **Node.js 18+**
- **MySQL Database**
- **Google Gemini API Key**

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/SalahKhadir/ChatBot.git
cd ChatBot/chatbot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
Create `.env` file in the `chatbot` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=mysql+pymysql://username:password@localhost/chatbot_db
SECRET_KEY=your_jwt_secret_key_here
SECURE_CV_FOLDER_PATH=C:/secure/cvs
```

5. **Database setup**
```bash
# Create MySQL database named 'chatbot_db'
# Tables will be created automatically on first run
```

6. **Start the backend server**
```bash
python main.py
# Server will run on http://localhost:8000
```

### Frontend Setup

1. **Navigate to interface directory**
```bash
cd ../interface
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
# Application will run on http://localhost:5173
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Chat Endpoints
- `POST /chat` - Authenticated chat (saves to database)
- `POST /chat/public` - Public chat (no persistence)
- `POST /analyze-document` - Authenticated document analysis
- `POST /analyze-document/public` - Public document analysis
- `POST /analyze-secure-folder` - **NEW**: Secure CV analysis from protected folders (authenticated only)

### Chat History Endpoints
- `GET /chat/history` - Get user's chat history
- `GET /chat/history/{session_id}` - Get specific chat session
- `DELETE /chat/history/{session_id}` - Delete chat session
- `DELETE /chat/history` - Clear all chat history
- `PUT /chat/history/{session_id}/title` - Update chat title

### Debug & Utilities
- `GET /debug/stats` - Database statistics (no auth required)
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **MySQL**: Relational database for data persistence
- **JWT**: JSON Web Tokens for authentication
- **Google Gemini**: Advanced AI language model
- **Pydantic**: Data validation using Python type annotations

### Frontend
- **React 19**: Modern UI library with hooks
- **Vite**: Fast build tool and development server
- **Axios**: Promise-based HTTP client
- **React Router**: Declarative routing
- **React Markdown**: Markdown rendering for AI responses

## 🔧 Configuration

### Database Models
- **User**: User accounts with authentication
- **ChatSession**: Individual chat conversations
- **Message**: Individual messages within sessions

### Environment Variables
```env
GEMINI_API_KEY=          # Google Gemini API key
DATABASE_URL=            # MySQL connection string
SECRET_KEY=              # JWT signing secret
SECURE_CV_FOLDER_PATH=   # Path to secure CV folder (for authenticated analysis)
```

## 📱 User Experience

### For Public Users
- ✅ Basic chat functionality
- ✅ PDF document analysis (via file upload)
- ✅ **Interactive section cards** with visual feedback
- ✅ **Quick start prompts** for creative writing, coding, and problem-solving
- ❌ No chat history (sessions are temporary)
- ❌ No data persistence
- ❌ **No secure folder access** or confidential CV analysis

### For Authenticated Users
- ✅ Full chat functionality with AI responses
- ✅ PDF document analysis with context preservation
- ✅ **Secure CV folder analysis** with protected file access
- ✅ Persistent chat history with ChatGPT-style sidebar
- ✅ Session management (create, delete, clear)
- ✅ Real-time history updates
- ✅ **Enhanced visual feedback** with active section states
- ✅ **Context-aware prompt suggestions** for all sections
- ✅ Personalized experience with full feature access

## 🚦 Development Workflow

### Running in Development
```bash
# Terminal 1: Backend
cd chatbot
python main.py

# Terminal 2: Frontend
cd interface
npm run dev
```

### Building for Production
```bash
# Frontend build
cd interface
npm run build

# Backend is production-ready with uvicorn
cd chatbot
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 About CGI

CGI (Compagnie générale immobilière) has been Morocco's leading real estate company since 1960, specializing in luxury properties, golf communities, and investment opportunities. This chatbot assistant embodies CGI's commitment to innovation and customer service excellence.

## 📞 Support

For support or questions about this project, please contact:
- **Developer**: Salah Khadir
- **GitHub**: [@SalahKhadir](https://github.com/SalahKhadir)
- **Project Repository**: [ChatBot](https://github.com/SalahKhadir/ChatBot)

---

**Built with ❤️ for CGI Real Estate**
