import { useState, useEffect } from 'react';
import { authService } from '../services/api';
import './Navbar.css';
import Login from './Login';
import Signup from './Signup';

function Navbar({ onHistoryToggle, isHistoryOpen, onThemeToggle, isDarkMode }) {
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  // Check authentication status on component mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = () => {
    const isLoggedIn = authService.isAuthenticated();
    setIsAuthenticated(isLoggedIn);
    
    if (isLoggedIn) {
      const userData = authService.getStoredUserData();
      setUser(userData);
    }
  };

  const handleLoginClick = () => {
    setShowLoginModal(true);
  };

  const handleLoginClose = () => {
    setShowLoginModal(false);
    // Check auth status in case user logged in
    const wasAuthenticated = isAuthenticated;
    checkAuthStatus();
    
    // Dispatch auth change event if status changed
    if (!wasAuthenticated && authService.isAuthenticated()) {
      window.dispatchEvent(new CustomEvent('authChanged'));
    }
  };

  const handleSignupClose = () => {
    setShowSignupModal(false);
    // Check auth status in case user signed up
    const wasAuthenticated = isAuthenticated;
    checkAuthStatus();
    
    // Dispatch auth change event if status changed
    if (!wasAuthenticated && authService.isAuthenticated()) {
      window.dispatchEvent(new CustomEvent('authChanged'));
    }
  };

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
    setUser(null);
    
    // Dispatch auth change event
    window.dispatchEvent(new CustomEvent('authChanged'));
    
    // Optionally refresh the page to clear any cached data
    window.location.reload();
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
            
            {/* Only show history button for authenticated users */}
            {isAuthenticated && (
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
            )}
            
            {isAuthenticated ? (
                <div className="user-info">
                    <span className="welcome-text">
                        Welcome, {user?.full_name || 'User'}!
                    </span>
                    <button className="logout-button" onClick={handleLogout}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                            <polyline points="16,17 21,12 16,7"/>
                            <line x1="21" y1="12" x2="9" y2="12"/>
                        </svg>
                        Logout
                    </button>
                </div>
            ) : (
                <button className="login-button" onClick={handleLoginClick}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M15 3h6v18h-6"/>
                        <path d="M10 17l5-5-5-5"/>
                        <path d="M3 12h12"/>
                    </svg>
                    Login
                </button>
            )}
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
