import { useState } from 'react';
import './Navbar.css';
import Login from './Login';
import Signup from './Signup';

function Navbar({ onHistoryToggle, isHistoryOpen, onThemeToggle, isDarkMode }) {
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSignupModal, setShowSignupModal] = useState(false);

  const handleLoginClick = () => {
    setShowLoginModal(true);
  };

  const handleLoginClose = () => {
    setShowLoginModal(false);
  };

  const handleSignupClose = () => {
    setShowSignupModal(false);
  };

  const handleSwitchToSignup = () => {
    setShowLoginModal(false);
    setShowSignupModal(true);
  };

  const handleSwitchToLogin = () => {
    setShowSignupModal(false);
    setShowLoginModal(true);
  };

return (
    <>
    <nav className={`navbar ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
        <div className="navbar-left">
            <div className="logo-container">
                <a href="/">
                    <img src="/src/assets/CGI_logo.png" alt="CGI Logo" className="logo" />
                </a>
            </div>
        </div>
        
        <div className="navbar-right">
            <div className="theme-toggle-container">
                <input 
                    type="checkbox" 
                    name="themeToggle" 
                    id="themeToggle" 
                    checked={isDarkMode}
                    onChange={onThemeToggle}
                />
                <label htmlFor="themeToggle" className="theme-toggle-label"></label>
            </div>
            
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
    
    {showLoginModal && (
      <Login 
        onClose={handleLoginClose} 
        isDarkMode={isDarkMode}
        onSwitchToSignup={handleSwitchToSignup}
      />
    )}
    
    {showSignupModal && (
      <Signup 
        onClose={handleSignupClose} 
        isDarkMode={isDarkMode}
        onSwitchToLogin={handleSwitchToLogin}
      />
    )}
    </>
  );
}

export default Navbar;
