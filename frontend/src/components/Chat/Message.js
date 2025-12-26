import React, { useState } from 'react';
import Rating from '../Common/Rating';
import './Message.css';

const Message = ({ message, isUser, onRate }) => {
  const [showRating, setShowRating] = useState(false);
  const [userRating, setUserRating] = useState(0);
  const [feedback, setFeedback] = useState('');

  const handleRate = (rating) => {
    setUserRating(rating);
    setShowRating(true);
  };

  const submitRating = () => {
    if (userRating > 0) {
      onRate(userRating, feedback);
      setShowRating(false);
      setFeedback('');
    }
  };

  if (!message.response && !isUser) return null;

  return (
    <div className={`message ${isUser ? 'user-message' : 'bot-message'}`}>
      <div className="message-content">
        {isUser ? (
          <div className="user-text">
            <p>{message.message}</p>
          </div>
        ) : (
          <div className="bot-text">
            <p>{message.response}</p>
            
            {!isUser && message.response && (
              <div className="message-actions">
                <button
                  className="rate-button"
                  onClick={() => handleRate(0)}
                  title="Оценить ответ"
                >
                  Оценить ответ
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {showRating && (
        <div className="rating-modal">
          <div className="rating-content">
            <h4>Оцените ответ</h4>
            <Rating
              value={userRating}
              onChange={setUserRating}
            />
            <textarea
              className="feedback-input"
              placeholder="Комментарий (необязательно)..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows="3"
            />
            <div className="rating-buttons">
              <button
                className="cancel-button"
                onClick={() => setShowRating(false)}
              >
                Отмена
              </button>
              <button
                className="submit-button"
                onClick={submitRating}
                disabled={userRating === 0}
              >
                Отправить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Message;