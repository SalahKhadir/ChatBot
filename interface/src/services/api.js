// API service for communicating with the backend
const API_BASE_URL = 'http://localhost:8000';

export const chatService = {
  // Send a simple text message
  async sendMessage(message) {
    const formData = new FormData();
    formData.append('message', message);
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    
    return response.json();
  },

  // Send a document for analysis
  async analyzeDocument(file, prompt) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('prompt', prompt);
    
    const response = await fetch(`${API_BASE_URL}/analyze-document`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to analyze document');
    }
    
    return response.json();
  }
};
