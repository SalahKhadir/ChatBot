import { useState } from 'react';
import { chatService } from '../services/api';
import { Navbar, HistorySidebar } from '../components';
import './Home.css';

function Home() {
  const [message, setMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

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
        // Use the first selected file for analysis
        response = await chatService.analyzeDocument(selectedFiles[0], message);
        
        // Add AI response to chat
        const aiMessage = { 
          type: 'ai', 
          content: response.response, 
          timestamp: new Date(),
          filename: response.filename 
        };
        setChatMessages(prev => [...prev, aiMessage]);
        
        // Clear selected files after analysis
        setSelectedFiles([]);
      } else {
        // Regular chat message
        response = await chatService.sendMessage(message);
        
        // Add AI response to chat
        const aiMessage = { 
          type: 'ai', 
          content: response.response, 
          timestamp: new Date() 
        };
        setChatMessages(prev => [...prev, aiMessage]);
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

  const handleHistoryToggle = () => {
    setIsHistoryOpen(!isHistoryOpen);
  };

  const handleHistoryClose = () => {
    setIsHistoryOpen(false);
  };

  return (
    <>
      <Navbar 
        onHistoryToggle={handleHistoryToggle} 
        isHistoryOpen={isHistoryOpen}
      />
      <HistorySidebar 
        isOpen={isHistoryOpen} 
        onClose={handleHistoryClose}
      />
      
      <div className={`home-container ${chatMessages.length > 0 ? 'chat-mode' : ''}`}>
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
              <div className="suggestion-card">
                <div className="suggestion-icon">💡</div>
                <h3>Creative Writing</h3>
                <p>Help with stories, essays, and creative content</p>
              </div>
              <div className="suggestion-card" onClick={triggerFileInput}>
                <div className="suggestion-icon">🔍</div>
                <h3>Research & Analysis</h3>
                <p>Get insights and analyze information</p>
                {selectedFiles.length > 0 && (
                  <div className="selected-files">
                    <p className="files-count">{selectedFiles.length} file(s) selected</p>
                    <div className="file-list">
                      {selectedFiles.map((file, index) => (
                        <span key={index} className="file-name">{file.name}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div className="suggestion-card">
                <div className="suggestion-icon">💻</div>
                <h3>Code & Development</h3>
                <p>Programming help and code reviews</p>
              </div>
              <div className="suggestion-card">
                <div className="suggestion-icon">🎯</div>
                <h3>Problem Solving</h3>
                <p>Break down complex problems step by step</p>
              </div>
            </div>
          </>
        ) : (
          <div className={`chat-messages ${chatMessages.length > 0 ? 'fullscreen' : ''}`}>
            {chatMessages.map((msg, index) => (
              <div key={index} className={`message ${msg.type}`}>
                {msg.type === 'user' && <div className="message-avatar user-avatar">You</div>}
                {msg.type === 'ai' && <div className="message-avatar ai-avatar">AI</div>}
                <div className="message-content">
                  {msg.filename && (
                    <div className="message-file">📄 Analyzing: {msg.filename}</div>
                  )}
                  <div className="message-text">{msg.content}</div>
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
