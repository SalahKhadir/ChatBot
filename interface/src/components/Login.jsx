import { useState } from 'react';
import { authService } from '../services/api';
import './Login.css';

function Login({ onClose, isDarkMode, onSwitchToSignup }) {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
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

    try {
      const response = await authService.login({
        email: formData.email,
        password: formData.password
      });

      console.log('✅ Login successful:', response);
      
      // Show success message
      setSuccess('Login successful! Welcome back.');
      
      // Close modal and refresh page after showing success message
      setTimeout(() => {
        onClose();
        window.location.reload();
      }, 1500);
      
    } catch (err) {
      console.error('❌ Login failed:', err);
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
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
          {error && (
            <div className="login-error" style={{ 
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
            <div className="login-success" style={{ 
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
          
          <span className="login-input-span">
            <label htmlFor="email" className="login-label">Email</label>
            <input 
              type="email" 
              name="email" 
              id="email" 
              value={formData.email}
              onChange={handleChange}
              required
              disabled={isLoading}
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
              disabled={isLoading}
              className="login-input"
            />
          </span>
          
          <span className="login-forgot-span">
            <a href="#" className="login-forgot-link">Forgot password?</a>
          </span>
          
          <input 
            className="login-submit" 
            type="submit" 
            value={isLoading ? "Signing in..." : "Log in"} 
            disabled={isLoading}
          />
          
          <span className="login-signup-span">
            Don't have an account? <a href="#" onClick={onSwitchToSignup} className="login-signup-link">Sign up</a>
          </span>
        </form>
      </div>
    </div>
  );
}

export default Login;
