import { useState } from 'react';
import { authService } from '../services/api';
import './Signup.css';

function Signup({ onClose, isDarkMode, onSwitchToLogin }) {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear messages when user types
    if (error) setError('');
    if (success) setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess('');
    
    // Basic validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }
    
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      setIsLoading(false);
      return;
    }

    try {
      const response = await authService.register({
        email: formData.email,
        full_name: formData.fullName,
        password: formData.password
      });

      console.log('✅ Registration successful:', response);
      
      // Show success message
      setSuccess('Account created successfully! Logging you in...');
      
      // Auto-login after successful registration
      await authService.login({
        email: formData.email,
        password: formData.password
      });
      
      // Close modal and refresh page after showing success message
      setTimeout(() => {
        onClose();
        window.location.reload();
      }, 2000);
      
    } catch (err) {
      console.error('❌ Registration failed:', err);
      setError(err.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
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
          {error && (
            <div className="signup-error" style={{ 
              color: '#ff4444', 
              padding: '8px', 
              marginBottom: '16px', 
              borderRadius: '4px', 
              backgroundColor: isDarkMode ? '#2a1a1a' : '#ffe6e6',
              border: '1px solid #ff4444'
            }}>
              {error}
            </div>
          )}
          
          {success && (
            <div className="signup-success" style={{ 
              color: '#22c55e', 
              padding: '8px', 
              marginBottom: '16px', 
              borderRadius: '4px', 
              backgroundColor: isDarkMode ? '#1a2a1a' : '#e6ffe6',
              border: '1px solid #22c55e'
            }}>
              {success}
            </div>
          )}
          
          <span className="signup-input-span">
            <label htmlFor="fullName" className="signup-label">Full Name</label>
            <input 
              type="text" 
              name="fullName" 
              id="fullName" 
              value={formData.fullName}
              onChange={handleChange}
              required
              disabled={isLoading}
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
              disabled={isLoading}
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
              disabled={isLoading}
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
              disabled={isLoading}
              className="signup-input"
            />
          </span>
          
          <input 
            className="signup-submit" 
            type="submit" 
            value={isLoading ? "Creating account..." : "Sign Up"} 
            disabled={isLoading}
          />
          
          <span className="signup-login-span">
            Already have an account? <a href="#" onClick={onSwitchToLogin} className="signup-login-link">Sign in</a>
          </span>
        </form>
      </div>
    </div>
  );
}

export default Signup;
