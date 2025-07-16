import { useState } from 'react';
import './Signup.css';

function Signup({ onClose, isDarkMode, onSwitchToLogin }) {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Basic validation
    if (formData.password !== formData.confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    
    // TODO: Implement signup logic
    console.log('Signup attempt:', formData);
    // For now, just close the modal
    onClose();
  };

  return (
    <div className={`signup-overlay ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
      <div className={`signup-modal ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
        <div className="signup-header">
          <h2 className="signup-title">Create Account</h2>
          <button className="signup-close-btn" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <form className="signup-form" onSubmit={handleSubmit}>
          <span className="signup-input-span">
            <label htmlFor="fullName" className="signup-label">Full Name</label>
            <input 
              type="text" 
              name="fullName" 
              id="fullName" 
              value={formData.fullName}
              onChange={handleChange}
              required
              className="signup-input"
            />
          </span>
          
          <span className="signup-input-span">
            <label htmlFor="email" className="signup-label">Email</label>
            <input 
              type="email" 
              name="email" 
              id="email" 
              value={formData.email}
              onChange={handleChange}
              required
              className="signup-input"
            />
          </span>
          
          <span className="signup-input-span">
            <label htmlFor="password" className="signup-label">Password</label>
            <input 
              type="password" 
              name="password" 
              id="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="signup-input"
            />
          </span>
          
          <span className="signup-input-span">
            <label htmlFor="confirmPassword" className="signup-label">Confirm Password</label>
            <input 
              type="password" 
              name="confirmPassword" 
              id="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              className="signup-input"
            />
          </span>
          
          <input className="signup-submit" type="submit" value="Sign Up" />
          
          <span className="signup-login-span">
            Already have an account? <a href="#" onClick={onSwitchToLogin} className="signup-login-link">Sign in</a>
          </span>
        </form>
      </div>
    </div>
  );
}

export default Signup;
