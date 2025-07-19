import React, { useState } from 'react';
import './HistorySidebar.css';

const HistorySidebar = ({ 
  isOpen,
  onClose,
  isDarkMode,
  onChatSelect, 
  onNewChat, 
  chatHistory, 
  currentChatId,
  onDeleteChat,
  onClearHistory,
  isLoading = false
}) => {
  const [isLoggedIn, setIsLoggedIn] = useState(true); // Auto-login for localStorage functionality

  const handleChatSelect = (chat) => {
    if (onChatSelect) {
      onChatSelect(chat);
    }
  };

  const handleNewChat = () => {
    if (onNewChat) {
      onNewChat();
    }
  };

  const handleDeleteChat = (e, chatId) => {
    e.stopPropagation(); // Prevent chat selection when deleting
    if (onDeleteChat) {
      onDeleteChat(chatId);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return 'Today';
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else if (diffInHours < 168) { // 7 days
      return `${Math.floor(diffInHours / 24)} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  if (!isOpen) return null;

  return (
    <div className={`history-sidebar ${isOpen ? 'open' : ''} ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
      <div className="history-header">
        <h3>Chat History</h3>
        <div className="header-buttons">
          <button 
            className="refresh-history-btn"
            onClick={() => window.location.reload()}
            title="Refresh history"
          >
            ↻
          </button>
          <button 
            className="new-chat-btn"
            onClick={handleNewChat}
            title="Start new chat"
          >
            +
          </button>
          <button className="close-button" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18"/>
              <path d="M6 6L18 18"/>
            </svg>
          </button>
        </div>
      </div>
      
      <div className="history-content">
        {!isLoggedIn ? (
          <div className="login-prompt">
            <div className="login-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <h4>Chat History Available</h4>
            <p>Your chat history is saved locally on this device</p>
            <button 
              className="login-prompt-button"
              onClick={() => setIsLoggedIn(true)}
            >
              Continue
            </button>
          </div>
        ) : (
          <div className="history-list">
            {isLoading ? (
              <div className="loading-history">
                <p>Loading chat history...</p>
              </div>
            ) : chatHistory.length === 0 ? (
              <div className="no-history">
                <p>No chat history yet.</p>
                <p>Start a conversation to see it here!</p>
              </div>
            ) : (
              chatHistory.map((chat) => (
                <div 
                  key={chat.id} 
                  className={`history-item ${chat.id === currentChatId ? 'active' : ''}`}
                  onClick={() => handleChatSelect(chat)}
                >
                  <div className="history-item-header">
                    <div className="history-title">{chat.title}</div>
                    <button 
                      className="delete-chat-btn"
                      onClick={(e) => handleDeleteChat(e, chat.id)}
                      title="Delete chat"
                    >
                      ×
                    </button>
                  </div>
                  <div className="history-meta">
                    <div className="history-date">{formatDate(chat.date)}</div>
                    <div className="history-count">{chat.messageCount} messages</div>
                  </div>
                  <div className="history-preview">{chat.preview}</div>
                  {chat.hasDocumentContext && (
                    <div className="document-context-badge">📄 With Documents</div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {chatHistory.length > 0 && isLoggedIn && (
          <div className="history-footer">
            <button 
              className="clear-history-btn"
              onClick={onClearHistory}
            >
              Clear All History
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistorySidebar;
