import api from './api';

export const login = async (username, password) => {
  const response = await api.post('/api/users/login', { username, password });
  return response.data;
};

export const register = async (userData) => {
  const response = await api.post('/api/users/register', userData);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/api/users/me');
  return response.data;
};

export const updateUserPreferences = async (preferences) => {
  const response = await api.put('/api/users/me', { preferences });
  return response.data;
};