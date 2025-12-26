import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Header.css';

const Header = () => {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="logo">
          <Link to="/">
            <h1>VenueBot</h1>
          </Link>
          <span className="tagline">Персональные рекомендации мест</span>
        </div>

        <nav className="nav-links">
          {isAuthenticated ? (
            <>
              <Link to="/chat" className="nav-link">
                Чат
              </Link>
              <Link to="/preferences" className="nav-link">
                Предпочтения
              </Link>
              
              {isAdmin && (
                <Link to="/admin" className="nav-link admin-link">
                  Админ-панель
                </Link>
              )}

              <div className="user-menu">
                <span className="username">{user?.username}</span>
                <button onClick={handleLogout} className="logout-button">
                  Выйти
                </button>
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link">
                Вход
              </Link>
              <Link to="/signup" className="nav-link signup-link">
                Регистрация
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};

export default Header;