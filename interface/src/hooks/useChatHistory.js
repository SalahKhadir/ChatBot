import { useState, useEffect } from 'react';
import { chatHistoryService } from '../services/chatHistoryService';

export const useChatHistory = () => {
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Load history from backend on mount
  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = async () => {
    try {
      setIsLoading(true);
      const response = await chatHistoryService.getChatHistory();
      
      // Transform backend response to frontend format
      const transformedHistory = response.chat_sessions.map(session => ({
        id: session.session_id,
        title: session.title,
        date: session.created_at,
        preview: session.preview,
        messages: [], // Will be loaded when needed
        messageCount: session.message_count,
        lastUpdated: session.updated_at || session.created_at,
        hasDocumentContext: session.has_document_context
      }));
      
      setChatHistory(transformedHistory);
    } catch (error) {
      console.error('Error loading chat history:', error);
      // Fallback to empty array on error
      setChatHistory([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Start a new chat session
  const startNewChat = () => {
    const newChatId = Date.now().toString(); // Temporary ID, backend will create proper session
    setCurrentChatId(newChatId);
    return newChatId;
  };

  // Load a chat from history
  const loadChatFromHistory = async (chatId) => {
    try {
      const response = await chatHistoryService.getChatSession(chatId);
      
      // Transform backend messages to frontend format
      const transformedMessages = response.messages.map(msg => ({
        type: msg.message_type,
        content: msg.content,
        timestamp: new Date(msg.created_at),
        hasDocumentContext: msg.has_document_context
      }));
      
      setCurrentChatId(chatId);
      return {
        messages: transformedMessages,
        title: response.title
      };
    } catch (error) {
      console.error('Error loading chat from history:', error);
      return null;
    }
  };

  // Delete a chat from history
  const deleteChatFromHistory = async (chatId) => {
    try {
      await chatHistoryService.deleteChatSession(chatId);
      // Reload chat history after deletion
      await loadChatHistory();
    } catch (error) {
      console.error('Error deleting chat from history:', error);
    }
  };

  // Clear all history
  const clearAllHistory = async () => {
    try {
      await chatHistoryService.clearChatHistory();
      setChatHistory([]);
    } catch (error) {
      console.error('Error clearing chat history:', error);
    }
  };

  // Update chat title
  const updateChatTitle = async (chatId, title) => {
    try {
      await chatHistoryService.updateChatTitle(chatId, title);
      // Reload chat history to reflect changes
      await loadChatHistory();
    } catch (error) {
      console.error('Error updating chat title:', error);
    }
  };

  // These functions are no longer needed for backend storage
  // but kept for compatibility
  const saveChatToHistory = () => {
    // Chat is automatically saved on the backend
    // Reload history to get latest data
    loadChatHistory();
  };

  const updateChatInHistory = () => {
    // Messages are automatically saved on the backend
    // Reload history periodically to keep it fresh
    loadChatHistory();
  };

  return {
    chatHistory,
    currentChatId,
    isLoading,
    startNewChat,
    loadChatFromHistory,
    deleteChatFromHistory,
    clearAllHistory,
    updateChatTitle,
    loadChatHistory,
    // Deprecated but kept for compatibility
    saveChatToHistory,
    updateChatInHistory,
    setCurrentChatId
  };
};
