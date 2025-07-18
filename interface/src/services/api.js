// API service for communicating with the backend
const API_BASE_URL = 'http://localhost:8000';

// Helper function to get auth token from localStorage
const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

// Helper function to create headers with auth token
const createHeaders = (includeAuth = false) => {
  const headers = {};
  if (includeAuth) {
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
};

export const chatService = {
  // Send a simple text message with optional session context (public endpoint)
  async sendMessage(message, sessionId = null) {
    const formData = new FormData();
    formData.append('message', message);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }
    
    const response = await fetch(`${API_BASE_URL}/chat/public`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    
    return response.json();
  },

  // Send authenticated message (requires login)
  async sendAuthenticatedMessage(message, sessionId = null) {
    const formData = new FormData();
    formData.append('message', message);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      body: formData,
      headers: createHeaders(true),
    });
    
    if (!response.ok) {
      throw new Error('Failed to send authenticated message');
    }
    
    return response.json();
  },

  // Send multiple documents for analysis (public endpoint)
  async analyzeDocument(files, prompt) {
    const formData = new FormData();
    
    // Add all files to the form data
    if (Array.isArray(files)) {
      files.forEach(file => {
        formData.append('files', file);
      });
    } else {
      // Single file compatibility
      formData.append('files', files);
    }
    
    formData.append('prompt', prompt);
    
    const response = await fetch(`${API_BASE_URL}/analyze-document/public`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to analyze document(s)');
    }
    
    return response.json();
  },

  // Send multiple documents for analysis (authenticated endpoint)
  async analyzeDocumentAuthenticated(files, prompt) {
    const formData = new FormData();
    
    // Add all files to the form data
    if (Array.isArray(files)) {
      files.forEach(file => {
        formData.append('files', file);
      });
    } else {
      // Single file compatibility
      formData.append('files', files);
    }
    
    formData.append('prompt', prompt);
    
    const response = await fetch(`${API_BASE_URL}/analyze-document`, {
      method: 'POST',
      body: formData,
      headers: createHeaders(true),
    });
    
    if (!response.ok) {
      throw new Error('Failed to analyze document(s)');
    }
    
    return response.json();
  }
};

export const authService = {
  // Register a new user
  async register(userData) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }
    
    return response.json();
  },

  // Login user
  async login(credentials) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }
    
    const data = await response.json();
    
    // Store token in localStorage
    localStorage.setItem('authToken', data.access_token);
    localStorage.setItem('userData', JSON.stringify(data.user));
    
    return data;
  },

  // Get current user info
  async getCurrentUser() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: createHeaders(true),
    });
    
    if (!response.ok) {
      throw new Error('Failed to get user info');
    }
    
    return response.json();
  },

  // Logout user
  logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
  },

  // Check if user is logged in
  isAuthenticated() {
    return !!getAuthToken();
  },

  // Get stored user data
  getStoredUserData() {
    const userData = localStorage.getItem('userData');
    return userData ? JSON.parse(userData) : null;
  }
};
