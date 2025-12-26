import React, { createContext, useState, useContext, useEffect } from 'react';
import { login as apiLogin, register as apiRegister, getCurrentUser } from '../services/auth';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const response = await apiLogin(username, password);
      localStorage.setItem('token', response.access_token);
      
      const userData = await getCurrentUser();
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      
      return { 
        success: true, 
        data: userData,
        hasPreferences: !!(userData.preferences && Object.keys(userData.preferences).length > 0)
      };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Не удалось войти в систему' 
      };
    }
  };

  const signup = async (userData) => {
    try {
      await apiRegister(userData);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Не удалось зарегистрироваться' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const updatePreferences = (preferences) => {
    const updatedUser = { ...user, preferences };
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      signup,
      logout,
      updatePreferences,
      isAuthenticated: !!user,
      isAdmin: user?.role === 'admin'
    }}>
      {children}
    </AuthContext.Provider>
  );
};