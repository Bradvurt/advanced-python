import React, { useState, useEffect, useRef } from 'react';
import { chatAPI, venuesAPI } from '../../services/api';
import Message from './Message';
import VenueCard from './VenueCard';
import Rating from '../Common/Rating';
import './Chat.css';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showVenues, setShowVenues] = useState([]);
  const [selectedVenue, setSelectedVenue] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadChatHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChatHistory = async () => {
    try {
      const response = await chatAPI.getHistory();
      const history = response.data;
      
      if (history.length > 0) {
        setMessages(history.reverse());
        setSessionId(history[0].session_id);
      } else {
        const newSessionId = `session_${Date.now()}`;
        setSessionId(newSessionId);
        
        // Add welcome message
        const welcomeMessage = {
          id: 0,
          message: '',
          response: "Привет! Я ваш персональный помощник по подбору мест. Чем могу помочь вам сегодня?",
          created_at: new Date().toISOString(),
          session_id: newSessionId
        };
        setMessages([welcomeMessage]);
      }
    } catch (error) {
      console.error('Не удалось загрузить историю чата:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      id: messages.length,
      message: inputMessage,
      response: '',
      created_at: new Date().toISOString(),
      isUser: true
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setShowVenues([]);

    try {
      const response = await chatAPI.sendMessage(inputMessage, sessionId);
      const data = response.data;

      const botMessage = {
        id: messages.length + 1,
        message: inputMessage,
        response: data.response,
        created_at: new Date().toISOString(),
        session_id: data.session_id,
        chat_id: messages.length + 1
      };

      setSessionId(data.session_id);
      setMessages(prev => [...prev, botMessage]);

      if (data.venues && data.venues.length > 0) {
        setShowVenues(data.venues);
      }

    } catch (error) {
      console.error('Не удалось отправить сообщение:', error);
      
      const errorMessage = {
        id: messages.length + 1,
        message: inputMessage,
        response: 'Произошла ошибка. Пожалуйста, попробуйте ещё раз.',
        created_at: new Date().toISOString(),
        session_id: sessionId
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleRateAnswer = async (chatId, rating, feedback = '') => {
    try {
      await chatAPI.rateAnswer(chatId, rating, feedback);
      alert('Спасибо за ваш отзыв!');
    } catch (error) {
      console.error('Не удалось оценить ответ:', error);
    }
  };

  const handleVenueSelect = async (venueId) => {
    try {
      const response = await venuesAPI.getVenue(venueId);
      setSelectedVenue(response.data);
    } catch (error) {
      console.error('Не удалось загрузить информацию о месте:', error);
    }
  };

  const handleRateVenue = async (venueId, rating, review) => {
    try {
      await venuesAPI.rateVenue(venueId, rating, review);
      alert('Спасибо за вашу оценку!');
      setSelectedVenue(null);
    } catch (error) {
      console.error('Не удалось оценить заведение:', error);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-main">
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <React.Fragment key={index}>
              {msg.message && (
                <Message
                  message={msg}
                  isUser={msg.isUser}
                  onRate={(rating, feedback) => 
                    handleRateAnswer(msg.chat_id || index, rating, feedback)
                  }
                />
              )}
              <Message
                message={msg}
                isUser={false}
                onRate={(rating, feedback) => 
                  handleRateAnswer(msg.chat_id || index, rating, feedback)
                }
              />
            </React.Fragment>
          ))}
          
          {loading && (
            <div className="message bot-message">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Рекомендованные места */}
        {showVenues.length > 0 && (
          <div className="suggested-venues">
            <h3>Рекомендованные места</h3>
            <div className="venues-grid">
              {showVenues.map(venue => (
                <VenueCard
                  key={venue.id}
                  venue={venue}
                  onSelect={() => handleVenueSelect(venue.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Поле ввода */}
        <form onSubmit={handleSendMessage} className="chat-input-form">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Спросите рекомендацию..."
            disabled={loading}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={loading || !inputMessage.trim()}
            className="send-button"
          >
            {loading ? '...' : 'Отправить'}
          </button>
        </form>
      </div>

      {/* Боковая панель с информацией о месте */}
      {selectedVenue && (
        <div className="venue-sidebar">
          <div className="sidebar-header">
            <button 
              className="close-sidebar"
              onClick={() => setSelectedVenue(null)}
            >
              ×
            </button>
            <h3>{selectedVenue.name}</h3>
            {selectedVenue.category && (
              <span className="venue-category">{selectedVenue.category}</span>
            )}
          </div>

          <div className="sidebar-content">
            {selectedVenue.rating > 0 && (
              <div className="venue-rating">
                <Rating value={selectedVenue.rating} readOnly />
                <span>({selectedVenue.review_count} отзывов)</span>
              </div>
            )}

            {selectedVenue.price_range && (
              <div className="venue-price">
                Цена: <strong>{selectedVenue.price_range}</strong>
              </div>
            )}

            {selectedVenue.description && (
              <div className="venue-description">
                <p>{selectedVenue.description}</p>
              </div>
            )}

            {selectedVenue.location && (
              <div className="venue-location">
                <h4>Адрес</h4>
                <p>{selectedVenue.location.address}</p>
              </div>
            )}

            {selectedVenue.amenities && selectedVenue.amenities.length > 0 && (
              <div className="venue-amenities">
                <h4>Удобства</h4>
                <div className="amenities-list">
                  {selectedVenue.amenities.map((amenity, idx) => (
                    <span key={idx} className="amenity-tag">{amenity}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Оценка места */}
            <div className="rating-form">
              <h4>Оценка места</h4>
              <Rating
                value={0}
                onChange={(rating) => {
                  const review = prompt('Добавьте отзыв (необязательно):');
                  if (rating > 0) {
                    handleRateVenue(selectedVenue.id, rating, review || '');
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatInterface;