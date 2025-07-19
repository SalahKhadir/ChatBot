import React from 'react';
import ReactMarkdown from 'react-markdown';
import { useTypingAnimation } from '../hooks/useTypingAnimation';

const TypingMessage = ({ content, isLatestMessage = false }) => {
  const { displayedText, isTyping } = useTypingAnimation(
    isLatestMessage ? content : content, 
    isLatestMessage ? 6 : 0 // Faster typing speed (6ms per character)
  );

  const textToShow = isLatestMessage ? displayedText : content;

  // If typing, add cursor directly to the text content
  if (isTyping && isLatestMessage) {
    const textWithCursor = textToShow + '<span class="typing-cursor">|</span>';
    return (
      <div className="message-text">
        <ReactMarkdown>{textToShow}</ReactMarkdown>
        <span className="typing-cursor">|</span>
      </div>
    );
  }

  return (
    <div className="message-text">
      <ReactMarkdown>{textToShow}</ReactMarkdown>
    </div>
  );
};

export default TypingMessage;
