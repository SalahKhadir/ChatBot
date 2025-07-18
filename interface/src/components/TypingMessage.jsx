import React from 'react';
import ReactMarkdown from 'react-markdown';
import { useTypingAnimation } from '../hooks/useTypingAnimation';

const TypingMessage = ({ content, isLatestMessage = false }) => {
  const { displayedText, isTyping } = useTypingAnimation(
    isLatestMessage ? content : content, 
    isLatestMessage ? 6 : 0 // Faster typing speed (6ms per character)
  );

  const textToShow = isLatestMessage ? displayedText : content;

  return (
    <div className="message-text" style={{ position: 'relative' }}>
      <ReactMarkdown>{textToShow}</ReactMarkdown>
      {isTyping && isLatestMessage && (
        <span 
          className="typing-cursor" 
          style={{ 
            position: 'absolute', 
            right: '0', 
            bottom: '0',
            transform: 'translateY(-2px)'
          }}
        >
          |
        </span>
      )}
    </div>
  );
};

export default TypingMessage;
