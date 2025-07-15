import './HistorySidebar.css';

function HistorySidebar({ isOpen, onClose }) {
  const isLoggedIn = false; // TODO: Replace with actual login state

  const mockHistory = [
    { id: 1, title: "Python coding help", date: "2024-01-15", preview: "How to create a FastAPI application..." },
    { id: 2, title: "Document analysis", date: "2024-01-14", preview: "Analyzing quarterly report..." },
    { id: 3, title: "Creative writing", date: "2024-01-13", preview: "Help with story structure..." },
  ];

  const handleHistoryClick = (historyItem) => {
    if (isLoggedIn) {
      // TODO: Load chat history
      console.log('Loading history:', historyItem);
    }
  };

  return (
    <div className={`history-sidebar ${isOpen ? 'open' : ''}`}>
      <div className="history-header">
        <h3>Chat History</h3>
        <button className="close-button" onClick={onClose}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18"/>
            <path d="M6 6L18 18"/>
          </svg>
        </button>
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
            <h4>Login Required</h4>
            <p>Please log in to view your chat history</p>
            <button className="login-prompt-button">
              Login
            </button>
          </div>
        ) : (
          <div className="history-list">
            {mockHistory.map((item) => (
              <div 
                key={item.id} 
                className="history-item"
                onClick={() => handleHistoryClick(item)}
              >
                <div className="history-title">{item.title}</div>
                <div className="history-date">{item.date}</div>
                <div className="history-preview">{item.preview}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default HistorySidebar;
