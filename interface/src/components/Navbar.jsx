import './Navbar.css';

function Navbar({ onHistoryToggle, isHistoryOpen }) {
  const handleLoginClick = () => {
    // TODO: Implement login functionality
    console.log('Login clicked');
  };

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <div className="logo-container">
          <img src="/src/assets/CGI_logo.png" alt="CGI Logo" className="logo" />
        </div>
      </div>
      
      <div className="navbar-right">
        <button 
          className="history-button"
          onClick={onHistoryToggle}
          title="Chat History"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 3h18v18H3V3z"/>
            <path d="M8 7h8"/>
            <path d="M8 11h8"/>
            <path d="M8 15h5"/>
          </svg>
        </button>
        
        <button className="login-button" onClick={handleLoginClick}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 3h6v18h-6"/>
            <path d="M10 17l5-5-5-5"/>
            <path d="M3 12h12"/>
          </svg>
          Login
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
