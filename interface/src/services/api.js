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
      if (response.status === 429) {
        // Rate limit exceeded
        const errorData = await response.json();
        const error = new Error(errorData.detail.message || 'Rate limit exceeded');
        error.rateLimitExceeded = true;
        error.requiresLogin = errorData.detail.requires_login;
        error.errorType = errorData.detail.type;
        throw error;
      }
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
      if (response.status === 429) {
        // Rate limit exceeded
        const errorData = await response.json();
        const error = new Error(errorData.detail.message || 'Rate limit exceeded');
        error.rateLimitExceeded = true;
        error.requiresLogin = errorData.detail.requires_login;
        error.errorType = errorData.detail.type;
        throw error;
      }
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
  },

  // Analyze documents from secure folder (authenticated users only)
  async analyzeSecureFolder(prompt) {
    const formData = new FormData();
    formData.append('prompt', prompt);
    
    const response = await fetch(`${API_BASE_URL}/analyze-secure-folder`, {
      method: 'POST',
      body: formData,
      headers: createHeaders(true),
    });
    
    if (!response.ok) {
      throw new Error('Failed to analyze secure folder documents');
    }
    
    return response.json();
  },

  // Check rate limit status for non-authenticated users
  async checkRateLimitStatus() {
    const response = await fetch(`${API_BASE_URL}/rate-limit/status`);
    
    if (!response.ok) {
      throw new Error('Failed to check rate limit status');
    }
    
    return await response.json();
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

// Admin API service
export const adminAPI = {
  // Get all users with statistics
  async getAllUsers() {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/admin/users`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch users');
    }
    
    return await response.json();
  },

  // Get platform statistics
  async getPlatformStats() {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/admin/stats`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }
    
    return await response.json();
  },

  // Update user role
  async updateUserRole(userId, newRole) {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/role`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ role: newRole }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update user role');
    }
    
    return await response.json();
  },

  // Update user status (active/inactive)
  async updateUserStatus(userId, isActive) {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/status`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ is_active: isActive }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update user status');
    }
    
    return await response.json();
  },

  // Delete user account
  async deleteUser(userId) {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete user');
    }
    
    return await response.json();
  },

  // Check if current user is admin
  isCurrentUserAdmin() {
    const userData = authService.getStoredUserData();
    return userData && userData.role === 'admin';
  },

  // Update user profile (for current user)
  async updateUserProfile(userId, profileData) {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/users/${userId}/profile`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profileData),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to update profile');
    }
    
    return await response.json();
  },

  // Change user password (for current user)
  async changeUserPassword(userId, passwordData) {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/users/${userId}/password`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(passwordData),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to change password');
    }
    
    return await response.json();
  },

  // Secure Folder Management

  // Get all secure folders and their contents
  async getSecureFolders() {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/admin/secure-folders`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch secure folders');
    }
    
    return await response.json();
  },

  // Upload files to secure folder
  async uploadToSecureFolder(files, folderName = 'default') {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const formData = new FormData();
    if (Array.isArray(files)) {
      files.forEach(file => {
        formData.append('files', file);
      });
    } else {
      formData.append('files', files);
    }
    formData.append('folder_name', folderName);

    const response = await fetch(`${API_BASE_URL}/admin/secure-folders/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to upload files to secure folder');
    }
    
    return await response.json();
  },

  // Delete file from secure folder
  async deleteFromSecureFolder(filename, folderName = 'default') {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/admin/secure-folders/delete`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        filename: filename,
        folder_name: folderName 
      }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete file from secure folder');
    }
    
    return await response.json();
  },

  // Get user permissions for secure folder access
  async getSecureFolderPermissions() {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/admin/secure-folders/permissions`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch secure folder permissions');
    }
    
    return await response.json();
  },

  // Update user permissions for secure folder access
  async updateSecureFolderPermissions(userId, hasAccess) {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/admin/secure-folders/permissions`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        user_id: userId,
        has_access: hasAccess 
      }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update secure folder permissions');
    }
    
    return await response.json();
  },

  // Check if current user has permission to access secure folder
  async checkSecureFolderPermission() {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token');

    const response = await fetch(`${API_BASE_URL}/user/secure-folder/permission`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to check secure folder permission');
    }
    
    return await response.json();
  }
};
