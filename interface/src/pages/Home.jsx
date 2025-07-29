import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatService, authService } from '../services/api';
import { Navbar, HistorySidebar, TypingMessage } from '../components';
import { useAutoScroll } from '../hooks/useAutoScroll';
import { useChatHistory } from '../hooks/useChatHistory';
import './Home.css';

function Home() {
  const [message, setMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [hasDocumentContext, setHasDocumentContext] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeSection, setActiveSection] = useState(null); // Track which section is active
  
  // Chat history hook (only used when authenticated)
  const {
    chatHistory,
    currentChatId,
    isLoading: isHistoryLoading,
    startNewChat,
    loadChatFromHistory,
    deleteChatFromHistory,
    clearAllHistory,
    loadChatHistory,
    setCurrentChatId
  } = useChatHistory();
  
  // Auto-scroll hook
  const messagesScrollRef = useAutoScroll([chatMessages, isLoading]);

  // Check authentication status on mount and when it changes
  useEffect(() => {
    const checkAuth = () => {
      const authStatus = authService.isAuthenticated();
      setIsAuthenticated(authStatus);
      
      if (authStatus) {
        // User is authenticated - start new chat with history
        const chatId = startNewChat();
        // Reset chat state
        setChatMessages([]);
        setCurrentSessionId(null);
        setHasDocumentContext(false);
        setSelectedFiles([]);
      } else {
        // User is not authenticated - clear everything and hide history
        setChatMessages([]);
        setCurrentSessionId(null);
        setHasDocumentContext(false);
        setSelectedFiles([]);
        setIsHistoryOpen(false); // Hide history sidebar for non-authenticated users
      }
    };
    
    checkAuth();
    
    // Listen for authentication changes (login/logout)
    const handleAuthChange = () => checkAuth();
    window.addEventListener('authChanged', handleAuthChange);
    
    return () => {
      window.removeEventListener('authChanged', handleAuthChange);
    };
  }, []);

  // Reload chat history periodically to keep it fresh (only when authenticated)
  useEffect(() => {
    if (!isAuthenticated) return;
    
    const interval = setInterval(() => {
      if (currentChatId && chatMessages.length > 0) {
        loadChatHistory(); // Refresh history to get latest updates
      }
    }, 30000); // Refresh every 30 seconds if there's an active chat

    return () => clearInterval(interval);
  }, [currentChatId, chatMessages.length, loadChatHistory]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setIsLoading(true);
    
    try {
      // Add user message to chat
      const userMessage = { type: 'user', content: message, timestamp: new Date() };
      setChatMessages(prev => [...prev, userMessage]);
      
      let response;
      
      // Check if there are files selected for analysis
      if (selectedFiles.length > 0) {
        // Use appropriate endpoint based on authentication
        if (isAuthenticated) {
          response = await chatService.analyzeDocumentAuthenticated(selectedFiles, message);
        } else {
          response = await chatService.analyzeDocument(selectedFiles, message);
        }
        
        // Set session context for future messages
        setCurrentSessionId(response.session_id);
        setHasDocumentContext(true);
        
        // Update current chat ID to match backend session (only if authenticated)
        if (isAuthenticated) {
          setCurrentChatId(response.session_id);
        }
        
        // Add AI response to chat with file information
        const aiMessage = { 
          type: 'ai', 
          content: response.response, 
          timestamp: new Date(),
          filesProcessed: response.files_processed,
          totalFiles: response.total_files,
          sessionId: response.session_id
        };
        setChatMessages(prev => [...prev, aiMessage]);
        
        // Clear selected files after analysis
        setSelectedFiles([]);
      } else if (isAuthenticated && activeSection === 'research') {
        // Use secure folder analysis for authenticated users in research section
        response = await chatService.analyzeSecureFolder(message);
        
        // Set session context for future messages
        setCurrentSessionId(response.session_id);
        setHasDocumentContext(true);
        setCurrentChatId(response.session_id);
        
        // Add AI response to chat with secure folder information
        const aiMessage = { 
          type: 'ai', 
          content: response.response, 
          timestamp: new Date(),
          filesProcessed: response.files_processed,
          totalFiles: response.total_files,
          sessionId: response.session_id,
          source: 'secure_folder'
        };
        setChatMessages(prev => [...prev, aiMessage]);
        
        // Reset active section after analysis
        setActiveSection(null);
      } else {
        // Regular chat message (with or without document context)
        // Use currentSessionId if we have one (continuing conversation)
        // or currentChatId if it's a real backend session
        const sessionToUse = currentSessionId || (currentChatId && currentChatId.length > 20 ? currentChatId : null);
        
        // Use appropriate endpoint based on authentication
        if (isAuthenticated) {
          response = await chatService.sendAuthenticatedMessage(message, sessionToUse);
        } else {
          response = await chatService.sendMessage(message, sessionToUse);
        }
        
        // Update session IDs from backend response (only if authenticated)
        if (isAuthenticated && response.session_id) {
          setCurrentSessionId(response.session_id);
          setCurrentChatId(response.session_id);
        } else if (!isAuthenticated && response.session_id) {
          // For non-authenticated users, only store session ID locally for document context
          setCurrentSessionId(response.session_id);
        }
        
        // Update document context status
        if (response.has_document_context !== undefined) {
          setHasDocumentContext(response.has_document_context);
        }
        
        // Add AI response to chat
        const aiMessage = { 
          type: 'ai', 
          content: response.response, 
          timestamp: new Date(),
          hasDocumentContext: response.has_document_context || false
        };
        setChatMessages(prev => [...prev, aiMessage]);
      }
      
      // Refresh chat history after sending message (only for authenticated users)
      if (isAuthenticated) {
        setTimeout(() => {
          if (loadChatHistory) {
            loadChatHistory();
          }
        }, 500); // Give the backend time to save the message
      }
      
      setMessage('');
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = { 
        type: 'error', 
        content: 'Sorry, something went wrong. Please try again.', 
        timestamp: new Date() 
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
    console.log('Selected files:', files);
    // You can add file processing logic here later
  };

  const triggerFileInput = () => {
    document.getElementById('fileInput').click();
  };

  // Section handlers
  const handleCreativeWriting = () => {
    setActiveSection('creative');
    setMessage('I need help with creative writing. Please suggest what type of content you can help me create.');
    // Auto-focus on input
    setTimeout(() => {
      document.querySelector('.message-input').focus();
    }, 100);
  };

  const handleCodeDevelopment = () => {
    setActiveSection('code');
    setMessage('I need help with code development. Please tell me what programming assistance you can provide.');
    setTimeout(() => {
      document.querySelector('.message-input').focus();
    }, 100);
  };

  const handleProblemSolving = () => {
    setActiveSection('problem');
    setMessage('I have a problem that needs solving. Please guide me on how you can help break it down step by step.');
    setTimeout(() => {
      document.querySelector('.message-input').focus();
    }, 100);
  };

  const handleResearchAnalysis = () => {
    setActiveSection('research');
    if (isAuthenticated) {
      // For authenticated users, prompt for secure folder analysis
      setMessage('Please describe what type of CV analysis you need from the secure folder.');
    } else {
      // For non-authenticated users, show file upload
      triggerFileInput();
    }
  };

  // Quick prompt templates
  const quickPrompts = {
    creative: [
      "Write a compelling property description for a luxury villa in Marrakech",
      "Create a blog post about Morocco's luxury real estate market trends",
      "Generate marketing copy for a golf community development",
      "Write an engaging social media post about CGI's heritage"
    ],
    code: [
      "Review my React component code for best practices",
      "Help me debug a JavaScript API integration issue",
      "Design a database schema for a property management system",
      "Create a Python script for real estate data analysis"
    ],
    problem: [
      "Analyze the pros and cons of investing in Moroccan real estate",
      "Break down the steps to launch a new property development",
      "Help me create a strategic plan for digital marketing",
      "Solve a complex business decision with multiple variables"
    ],
    research: [
      "Analyze CVs for a specific role and rank candidates by suitability",
      "Compare candidate skills and experience for senior positions",
      "Extract key qualifications and technical skills from resumes",
      "Provide detailed candidate recommendations with strengths and gaps"
    ]
  };

  const handleQuickPrompt = (prompt) => {
    setMessage(prompt);
    setTimeout(() => {
      document.querySelector('.message-input').focus();
    }, 100);
  };

  const handleHistoryToggle = () => {
    // Only allow history toggle for authenticated users
    if (isAuthenticated) {
      setIsHistoryOpen(!isHistoryOpen);
    }
  };

  const handleHistoryClose = () => {
    setIsHistoryOpen(false);
  };

  const handleThemeToggle = () => {
    setIsDarkMode(!isDarkMode);
  };

  // Chat history handlers
  const handleChatSelect = async (chat) => {
    try {
      const loadedChat = await loadChatFromHistory(chat.id);
      if (loadedChat) {
        // Mark all loaded messages as from history to skip typing animation
        const messagesWithHistoryFlag = loadedChat.messages.map(msg => ({
          ...msg,
          isFromHistory: true // Add flag to indicate this message is from history
        }));
        
        setChatMessages(messagesWithHistoryFlag);
        // Set the session ID to the loaded chat ID for continuing conversation
        setCurrentSessionId(chat.id);
        // Reset other state
        setHasDocumentContext(loadedChat.messages.some(msg => msg.hasDocumentContext));
        setSelectedFiles([]);
        setIsHistoryOpen(false);
      }
    } catch (error) {
      console.error('Error loading chat:', error);
    }
  };

  const handleNewChat = () => {
    const newChatId = startNewChat();
    // Reset all chat state
    setChatMessages([]);
    setCurrentSessionId(null);
    setHasDocumentContext(false);
    setSelectedFiles([]);
    setIsHistoryOpen(false);
  };

  const handleDeleteChat = async (chatId) => {
    try {
      await deleteChatFromHistory(chatId);
      // If we're deleting the current chat, start a new one
      if (chatId === currentChatId) {
        handleNewChat();
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  const handleClearHistory = async () => {
    if (confirm('Are you sure you want to clear all chat history? This action cannot be undone.')) {
      try {
        await clearAllHistory();
        handleNewChat();
      } catch (error) {
        console.error('Error clearing history:', error);
      }
    }
  };

  return (
    <>
      <Navbar 
        onHistoryToggle={handleHistoryToggle} 
        isHistoryOpen={isHistoryOpen}
        onThemeToggle={handleThemeToggle}
        isDarkMode={isDarkMode}
      />
      {/* Only show history sidebar for authenticated users */}
      {isAuthenticated && (
        <HistorySidebar 
          isOpen={isHistoryOpen} 
          onClose={handleHistoryClose}
          isDarkMode={isDarkMode}
          onChatSelect={handleChatSelect}
          onNewChat={handleNewChat}
          chatHistory={chatHistory}
          currentChatId={currentChatId}
          onDeleteChat={handleDeleteChat}
          onClearHistory={handleClearHistory}
          isLoading={isHistoryLoading}
        />
      )}
      
      <div className={`home-container ${chatMessages.length > 0 ? 'chat-mode' : ''} ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
        <div className={`home-content ${chatMessages.length > 0 ? 'chat-mode' : ''}`}>
        {chatMessages.length === 0 ? (
          <>
            <div className="hero-section">
              <h1 className="hero-title">
                Welcome to Your AI Assistant
              </h1>
              <p className="hero-subtitle">
                How can I help you today?
              </p>
            </div>

            <div className="suggestions-grid">
              <div className={`suggestion-card ${activeSection === 'creative' ? 'active' : ''}`} onClick={handleCreativeWriting}>
                <div className="suggestion-icon">💡</div>
                <h3>Creative Writing</h3>
                <p>Help with stories, essays, and creative content</p>
                <div className="card-examples">
                  <small>• Property descriptions • Marketing copy • Blog posts</small>
                </div>
              </div>
              <div className={`suggestion-card ${activeSection === 'research' ? 'active' : ''}`} onClick={handleResearchAnalysis}>
                <div className="suggestion-icon">🔍</div>
                <h3>Research & Analysis</h3>
                {isAuthenticated ? (
                  <p>Analyze CVs from secure folder with confidential access</p>
                ) : (
                  <p>Upload multiple PDFs for comprehensive analysis</p>
                )}
                {selectedFiles.length > 0 && (
                  <div className="selected-files">
                    <p className="files-count">{selectedFiles.length} file(s) selected</p>
                  </div>
                )}
                <div className="card-examples">
                  {isAuthenticated ? (
                    <small>• CV analysis • Candidate ranking • Skills extraction</small>
                  ) : (
                    <small>• Document analysis • Data extraction • Summarization</small>
                  )}
                </div>
              </div>
              <div className={`suggestion-card ${activeSection === 'code' ? 'active' : ''}`} onClick={handleCodeDevelopment}>
                <div className="suggestion-icon">💻</div>
                <h3>Code & Development</h3>
                <p>Programming help and code reviews</p>
                <div className="card-examples">
                  <small>• Code review • Bug fixing • API development</small>
                </div>
              </div>
              <div className={`suggestion-card ${activeSection === 'problem' ? 'active' : ''}`} onClick={handleProblemSolving}>
                <div className="suggestion-icon">🎯</div>
                <h3>Problem Solving</h3>
                <p>Break down complex problems step by step</p>
                <div className="card-examples">
                  <small>• Business analysis • Technical troubleshooting • Strategy</small>
                </div>
              </div>
            </div>

            {/* Quick Prompts Section */}
            {activeSection && !(activeSection === 'research' && !isAuthenticated) && (
              <div className="quick-prompts-section">
                <h3>Quick Start Prompts</h3>
                <div className="quick-prompts-grid">
                  {quickPrompts[activeSection]?.map((prompt, index) => (
                    <div 
                      key={index} 
                      className="quick-prompt-card"
                      onClick={() => handleQuickPrompt(prompt)}
                    >
                      <span className="prompt-icon">💡</span>
                      <p>{prompt}</p>
                    </div>
                  ))}
                </div>
                <button 
                  className="clear-selection-btn"
                  onClick={() => setActiveSection(null)}
                >
                  ← Back to all sections
                </button>
              </div>
            )}
          </>
        ) : (
          <div ref={messagesScrollRef} className={`chat-messages ${chatMessages.length > 0 ? 'fullscreen' : ''}`}>
            {chatMessages.map((msg, index) => (
              <div key={index} className={`message ${msg.type}`}>
                {msg.type === 'user' && <div className="message-avatar user-avatar">You</div>}
                {msg.type === 'ai' && <div className="message-avatar ai-avatar">AI</div>}
                <div className="message-content">
                  {msg.filesProcessed && (
                    <div className="message-files">
                      <div className="files-header">
                        {msg.source === 'secure_folder' ? (
                          <span>� Analyzed {msg.totalFiles} confidential document{msg.totalFiles > 1 ? 's' : ''} from secure folder:</span>
                        ) : (
                          <span>�📄 Analyzed {msg.totalFiles} document{msg.totalFiles > 1 ? 's' : ''}:</span>
                        )}
                      </div>
                      <div className="files-list">
                        {msg.filesProcessed.map((file, fileIndex) => (
                          <div key={fileIndex} className="file-item">
                            • {file.filename} ({(file.size / 1024).toFixed(1)} KB)
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {msg.filename && (
                    <div className="message-file">📄 Analyzing: {msg.filename}</div>
                  )}
                  {msg.hasDocumentContext && (
                    <div className="message-context-indicator">
                      <span className="context-badge">📄 Document Context</span>
                    </div>
                  )}
                  {msg.type === 'ai' ? (
                    msg.isFromHistory ? (
                      // For messages loaded from history, show instantly without typing animation
                      <div className="message-text">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      // For new messages, use typing animation
                      <TypingMessage 
                        content={msg.content} 
                        isLatestMessage={index === chatMessages.length - 1}
                      />
                    )
                  ) : (
                    <div className="message-text">{msg.content}</div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message ai">
                <div className="message-avatar ai-avatar">AI</div>
                <div className="message-content">
                  <div className="message-text loading">Thinking...</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Hidden file input */}
        <input
          type="file"
          id="fileInput"
          style={{ display: 'none' }}
          multiple
          accept=".pdf,.doc,.docx,.txt,.rtf"
          onChange={handleFileUpload}
        />

        <div className={`chat-input-container ${chatMessages.length > 0 ? 'fullscreen' : ''}`}>
          {/* Document Context Indicator */}
          {hasDocumentContext && (
            <div className="document-context-indicator">
              <div className="context-icon">📄</div>
              <span>Chat has document context - AI can reference uploaded documents</span>
              <button 
                type="button" 
                onClick={() => {
                  setCurrentSessionId(null);
                  setHasDocumentContext(false);
                }}
                className="clear-context-btn"
                title="Clear document context"
              >
                Clear Context
              </button>
            </div>
          )}
          
          {/* Selected Files Display */}
          {selectedFiles.length > 0 && (
            <div className="selected-files-container">
              <div className="selected-files-header">
                <span>Selected Files ({selectedFiles.length}):</span>
                <button 
                  type="button" 
                  onClick={() => setSelectedFiles([])}
                  className="clear-files-btn"
                >
                  Clear All
                </button>
              </div>
              <div className="selected-files-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="selected-file-item">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
                    <button 
                      type="button"
                      onClick={() => {
                        const newFiles = selectedFiles.filter((_, i) => i !== index);
                        setSelectedFiles(newFiles);
                      }}
                      className="remove-file-btn"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="chat-form">
            <div className="input-wrapper">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask me anything..."
                className="chat-input"
              />
              <button 
                type="submit" 
                className="send-button-animated"
                disabled={!message.trim() || isLoading}
              >
                <div className="svg-wrapper-1-send">
                  <div className="svg-wrapper-send">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      width="24"
                      height="24"
                    >
                      <path fill="none" d="M0 0h24v24H0z"></path>
                      <path
                        fill="currentColor"
                        d="M1.946 9.315c-.522-.174-.527-.455.01-.634l19.087-6.362c.529-.176.832.12.684.638l-5.454 19.086c-.15.529-.455.547-.679.045L12 14l6-8-8 6-8.054-2.685z"
                      ></path>
                    </svg>
                  </div>
                </div>
                <span className="send-button-text">
                  {isLoading ? 'Sending...' : 'Send'}
                </span>
              </button>
            </div>
          </form>
        </div>
        </div>
      </div>
    </>
  );
}

export default Home;
