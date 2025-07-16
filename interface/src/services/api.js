// API service for communicating with the backend
const API_BASE_URL = 'http://localhost:8000';

export const chatService = {
  // Send a simple text message with optional session context
  async sendMessage(message, sessionId = null) {
    const formData = new FormData();
    formData.append('message', message);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    
    return response.json();
  },

  // Send multiple documents for analysis
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
    
    const response = await fetch(`${API_BASE_URL}/analyze-document`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to analyze document(s)');
    }
    
    return response.json();
  }
};
