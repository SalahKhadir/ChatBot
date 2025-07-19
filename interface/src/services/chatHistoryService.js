import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with auth token
const createAuthenticatedRequest = () => {
  const token = localStorage.getItem('authToken');
  return axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json'
    }
  });
};

export const chatHistoryService = {
  // Get user's chat history
  async getChatHistory(skip = 0, limit = 50) {
    try {
      const api = createAuthenticatedRequest();
      const response = await api.get(`/chat/history?skip=${skip}&limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching chat history:', error);
      throw error;
    }
  },

  // Get a specific chat session with messages
  async getChatSession(sessionId) {
    try {
      const api = createAuthenticatedRequest();
      const response = await api.get(`/chat/history/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching chat session:', error);
      throw error;
    }
  },

  // Delete a specific chat session
  async deleteChatSession(sessionId) {
    try {
      const api = createAuthenticatedRequest();
      const response = await api.delete(`/chat/history/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting chat session:', error);
      throw error;
    }
  },

  // Clear all chat history
  async clearChatHistory() {
    try {
      const api = createAuthenticatedRequest();
      const response = await api.delete('/chat/history');
      return response.data;
    } catch (error) {
      console.error('Error clearing chat history:', error);
      throw error;
    }
  },

  // Update chat session title
  async updateChatTitle(sessionId, title) {
    try {
      const api = createAuthenticatedRequest();
      const formData = new FormData();
      formData.append('title', title);
      
      const response = await api.put(`/chat/history/${sessionId}/title`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error updating chat title:', error);
      throw error;
    }
  }
};
