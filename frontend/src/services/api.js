import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Перехватчик запросов для добавления токена авторизации
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Перехватчик ответов для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API для чата
export const chatAPI = {
  sendMessage: (message, sessionId = null) =>
    api.post('/api/chat/message', { message, session_id: sessionId }),
  
  getHistory: (sessionId = null, limit = 50) =>
    api.get('/api/chat/history', { params: { session_id: sessionId, limit } }),
  
  rateAnswer: (chatId, rating, feedback = '') =>
    api.post('/api/chat/rate-answer', { chat_id: chatId, rating, feedback }),
};

// API для заведений
export const venuesAPI = {
  getVenues: (params) => api.get('/api/venues', { params }),
  
  getVenue: (venueId) => api.get(`/api/venues/${venueId}`),
  
  rateVenue: (venueId, rating, review = '') =>
    api.post(`/api/venues/${venueId}/rate`, { venue_id: venueId, rating, review }),
  
  getReviews: (venueId, limit = 10, offset = 0) =>
    api.get(`/api/venues/${venueId}/reviews`, { params: { limit, offset } }),
};

// Admin API
export const adminAPI = {
  parseVenues: (config) => api.post('/api/admin/parse-venues', config),
  
  getUnmoderatedRatings: (limit = 50) =>
    api.get('/api/admin/unmoderated-ratings', { params: { limit } }),
  
  moderateRating: (ratingId, approve = true) =>
    api.post(`/api/admin/moderate-rating/${ratingId}`, { approve }),
  
  getUsers: (params) => api.get('/api/admin/users', { params }),
  
  toggleUserActive: (userId) => api.post(`/api/admin/users/${userId}/toggle-active`),
  
  getStats: () => api.get('/api/admin/stats'),
};

// API для пользователей
export const userAPI = {
  // Существующие эндпоинты
  updatePreferences: (preferences) => 
    api.put('/api/users/me', { preferences }),
  
  // Новые эндпоинты
  getPreferences: () => api.get('/api/users/me/preferences'),
  
  getChatHistory: (limit = 50, offset = 0) =>
    api.get('/api/users/me/history', { params: { limit, offset } }),
  
  getRatings: () => api.get('/api/users/me/ratings'),
  
  getStats: () => api.get('/api/users/me/stats'),
  
  // Админские эндпоинты для управления пользователями
  searchUsers: (params) => api.get('/api/users/search', { params }),
  
  getUser: (userId) => api.get(`/api/users/${userId}`),
  
  updateUser: (userId, userData) => 
    api.put(`/api/users/${userId}`, userData),
  
  deleteUser: (userId) => api.delete(`/api/users/${userId}`),
};

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;