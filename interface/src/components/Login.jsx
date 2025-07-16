import { useState } from 'react';
import './Login.css';

function Login({ onClose, isDarkMode, onSwitchToSignup }) {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Implement login logic
    console.log('Login attempt:', formData);
    // For now, just close the modal
    onClose();
  };

  return (
    <div className={`login-overlay ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
      <div className={`login-modal ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
        <div className="login-header">
          <h2 className="login-title">Sign In</h2>
          <button className="modal-close-btn" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <form className="login-form" onSubmit={handleSubmit}>
          <span className="login-input-span">
            <label htmlFor="email" className="login-label">Email</label>
            <input 
              type="email" 
              name="email" 
              id="email" 
              value={formData.email}
              onChange={handleChange}
              required
              className="login-input"
            />
          </span>
          
          <span className="login-input-span">
            <label htmlFor="password" className="login-label">Password</label>
            <input 
              type="password" 
              name="password" 
              id="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="login-input"
            />
          </span>
          
          <span className="login-forgot-span">
            <a href="#" className="login-forgot-link">Forgot password?</a>
          </span>
          
          <input className="login-submit" type="submit" value="Log in" />
          
          <span className="login-signup-span">
            Don't have an account? <a href="#" onClick={onSwitchToSignup} className="login-signup-link">Sign up</a>
          </span>
        </form>
      </div>
    </div>
  );
}

export default Login;
