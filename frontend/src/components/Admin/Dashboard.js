import React, { useState, useEffect } from 'react';
import { adminAPI } from '../../services/api';
import ParserControl from './ParserControl';
import UserManagement from './UserManagement';
import Rating from '../Common/Rating';
import './Dashboard.css';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [unmoderatedRatings, setUnmoderatedRatings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsRes, ratingsRes] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getUnmoderatedRatings(10)
      ]);
      
      setStats(statsRes.data);
      setUnmoderatedRatings(ratingsRes.data);
    } catch (error) {
      console.error('Ошибка при загрузке данных панели управления:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleModerateRating = async (ratingId, approve) => {
    try {
      await adminAPI.moderateRating(ratingId, approve);
      setUnmoderatedRatings(prev => 
        prev.filter(rating => rating.id !== ratingId)
      );
    } catch (error) {
      console.error('Ошибка при модерации отзыва:', error);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading-spinner">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>Панель управления</h2>
        <div className="dashboard-tabs">
          <button
            className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Обзор
          </button>
          <button
            className={`tab-button ${activeTab === 'parser' ? 'active' : ''}`}
            onClick={() => setActiveTab('parser')}
          >
            Загрузка данных
          </button>
          <button
            className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            Пользователи
          </button>
          <button
            className={`tab-button ${activeTab === 'moderation' ? 'active' : ''}`}
            onClick={() => setActiveTab('moderation')}
          >
           Модерация
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="overview-section">
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Всего пользователей</h3>
                <p className="stat-number">{stats?.total_users || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Всего заведений</h3>
                <p className="stat-number">{stats?.total_venues || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Всего диалогов</h3>
                <p className="stat-number">{stats?.total_chats || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Всего отзывов</h3>
                <p className="stat-number">{stats?.total_ratings || 0}</p>
              </div>
            </div>

            <div className="moderation-preview">
              <h3>Ожидают проверки</h3>
              {unmoderatedRatings.length === 0 ? (
                <p className="no-data">Нет отзывов на проверке</p>
              ) : (
                <div className="ratings-list">
                  {unmoderatedRatings.map(rating => (
                    <div key={rating.id} className="rating-item">
                      <div className="rating-info">
                        <strong>Оценка: {rating.rating}/5</strong>
                        <p>{rating.review?.substring(0, 100)}...</p>
                      </div>
                      <div className="rating-actions">
                        <button
                          className="approve-button"
                          onClick={() => handleModerateRating(rating.id, true)}
                        >
                          Одобрить
                        </button>
                        <button
                          className="reject-button"
                          onClick={() => handleModerateRating(rating.id, false)}
                        >
                          Отклонить
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'parser' && <ParserControl />}
        {activeTab === 'users' && <UserManagement />}
        
        {activeTab === 'moderation' && (
          <div className="moderation-section">
            <h3>Модерация отзывов</h3>
            <div className="moderation-list">
              {unmoderatedRatings.map(rating => (
                <div key={rating.id} className="moderation-item">
                  <div className="moderation-content">
                    <div className="user-info">
                      <span>Пользователь ID: {rating.user_id}</span>
                      <span>Заведение ID: {rating.venue_id}</span>
                    </div>
                    <div className="rating-content">
                      <Rating value={rating.rating} readOnly />
                      <p className="review-text">{rating.review}</p>
                    </div>
                  </div>
                  <div className="moderation-buttons">
                    <button
                      className="approve-button"
                      onClick={() => handleModerateRating(rating.id, true)}
                    >
                      ✓ Одобрить
                    </button>
                    <button
                      className="reject-button"
                      onClick={() => handleModerateRating(rating.id, false)}
                    >
                      ✗ Отклонить
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;