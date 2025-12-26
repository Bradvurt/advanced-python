import React, { useState, useEffect } from 'react';
import { adminAPI } from '../../services/api';
import './UserManagement.css';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  
  const pageSize = 10;

  useEffect(() => {
    loadUsers();
  }, [currentPage, roleFilter, activeFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const params = {
        limit: pageSize,
        role: roleFilter || undefined,
        is_active: activeFilter === 'true' ? true : activeFilter === 'false' ? false : undefined
      };
      
      const response = await adminAPI.getUsers(params);
      setUsers(response.data);
      setTotalPages(Math.ceil(response.data.length / pageSize));
    } catch (error) {
      console.error('Ошибка при загрузке пользователей:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (userId) => {
    try {
      await adminAPI.toggleUserActive(userId);
      await loadUsers(); // Reload users
    } catch (error) {
      console.error('Ошибка при изменении статуса пользователя:', error);
    }
  };

  const handleSearch = async () => {
    setCurrentPage(1);
    await loadUsers();
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setShowEditModal(true);
  };

  const handleSaveUser = async (updatedUser) => {
    try {
      // Implement user update API if available
      console.log('Save user:', updatedUser);
      setShowEditModal(false);
      await loadUsers();
    } catch (error) {
      console.error('Ошибка при обновлении данных пользователя:', error);
    }
  };

  const filteredUsers = users.filter(user => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      user.username.toLowerCase().includes(searchLower) ||
      user.email.toLowerCase().includes(searchLower) ||
      user.role.toLowerCase().includes(searchLower)
    );
  });

  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  if (loading) {
    return (
      <div className="user-management">
        <div className="loading-spinner">Загрузка пользователей...</div>
      </div>
    );
  }

  return (
    <div className="user-management">
      <div className="user-management-header">
        <h3>Управление пользователями</h3>
        <p className="subtitle">Управление аккаунтами и правами доступа</p>
      </div>

      {/* Filters and Search */}
      <div className="user-filters">
        <div className="search-box">
          <input
            type="text"
            placeholder="Поиск по имени, email или роли..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} className="search-button">
            🔍
          </button>
        </div>

        <div className="filter-controls">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">Все роли</option>
            <option value="user">Пользователи</option>
            <option value="admin">Администраторы</option>
          </select>

          <select
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">Все статусы</option>
            <option value="true">Активные</option>
            <option value="false">Неактивные</option>
          </select>

          <button onClick={loadUsers} className="refresh-button">
            Обновить
          </button>
        </div>
      </div>

      {/* Users Table */}
      <div className="users-table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Имя пользователя</th>
              <th>Email</th>
              <th>Роль</th>
              <th>Статус</th>
              <th>Дата регистрации</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {paginatedUsers.length === 0 ? (
              <tr>
                <td colSpan="7" className="no-data">
                  Пользователи не найдены
                </td>
              </tr>
            ) : (
              paginatedUsers.map(user => (
                <tr key={user.id} className={user.is_active ? '' : 'inactive'}>
                  <td className="user-id">#{user.id}</td>
                  <td className="user-username">
                    <div className="user-avatar">
                      {user.username.charAt(0).toUpperCase()}
                    </div>
                    {user.username}
                  </td>
                  <td className="user-email">{user.email}</td>
                  <td>
                    <span className={`role-badge role-${user.role}`}>
                      {user.role}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge status-${user.is_active ? 'active' : 'inactive'}`}>
                      {user.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                  </td>
                  <td className="user-joined">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="user-actions">
                    <button
                      onClick={() => handleEditUser(user)}
                      className="action-button edit-button"
                      title="Редактировать пользователя"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => handleToggleActive(user.id)}
                      className={`action-button toggle-button ${user.is_active ? 'deactivate' : 'activate'}`}
                      title={user.is_active ? 'Деактивировать' : 'Активировать'}
                    >
                      {user.is_active ? '⏸️' : '▶️'}
                    </button>
                    <button
                      className="action-button view-button"
                      title="Просмотреть детали"
                      onClick={() => setSelectedUser(user)}
                    >
                      👁️
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="page-button"
          >
            ← Назад
          </button>
          
          <span className="page-info">
            Страница {currentPage} из {totalPages}
          </span>
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="page-button"
          >
            Вперёд →
          </button>
        </div>
      )}

      {/* User Detail Modal */}
      {selectedUser && !showEditModal && (
        <div className="modal-overlay" onClick={() => setSelectedUser(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h4>Информация о пользователе</h4>
              <button
                className="modal-close"
                onClick={() => setSelectedUser(null)}
              >
                ×
              </button>
            </div>
            
            <div className="user-details">
              <div className="detail-row">
                <span className="detail-label">Имя пользователя:</span>
                <span className="detail-value">{selectedUser.username}</span>
              </div>
              
              <div className="detail-row">
                <span className="detail-label">Email:</span>
                <span className="detail-value">{selectedUser.email}</span>
              </div>
              
              <div className="detail-row">
                <span className="detail-label">Роль:</span>
                <span className={`detail-value role-badge role-${selectedUser.role}`}>
                  {selectedUser.role}
                </span>
              </div>
              
              <div className="detail-row">
                <span className="detail-label">Статус:</span>
                <span className={`detail-value status-badge status-${selectedUser.is_active ? 'active' : 'inactive'}`}>
                  {selectedUser.is_active ? 'Активен' : 'Неактивен'}
                </span>
              </div>
              
              <div className="detail-row">
                <span className="detail-label">Дата регистрации:</span>
                <span className="detail-value">
                  {new Date(selectedUser.created_at).toLocaleString()}
                </span>
              </div>
              
              {selectedUser.preferences && Object.keys(selectedUser.preferences).length > 0 && (
                <div className="detail-row">
                  <span className="detail-label">Предпочтения:</span>
                  <div className="detail-value preferences">
                    {Object.entries(selectedUser.preferences).map(([key, value]) => (
                      <div key={key} className="preference-item">
                        <strong>{key}:</strong> {JSON.stringify(value)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="modal-actions">
              <button
                onClick={() => {
                  setShowEditModal(true);
                  setSelectedUser(null);
                }}
                className="edit-user-button"
              >
                Редактировать
              </button>
              <button
                onClick={() => setSelectedUser(null)}
                className="close-modal-button"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal-content edit-modal">
            <div className="modal-header">
              <h4>Редактирование пользователя</h4>
              <button
                className="modal-close"
                onClick={() => setShowEditModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="edit-form">
              <div className="form-group">
                <label htmlFor="edit-username">Имя пользователя</label>
                <input
                  id="edit-username"
                  type="text"
                  defaultValue={selectedUser?.username}
                  placeholder="Username"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="edit-email">Email</label>
                <input
                  id="edit-email"
                  type="email"
                  defaultValue={selectedUser?.email}
                  placeholder="Email"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="edit-role">Роль</label>
                <select
                  id="edit-role"
                  defaultValue={selectedUser?.role}
                >
                  <option value="user">Пользователь</option>
                  <option value="admin">Администратор</option>
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="edit-status">Статус</label>
                <select
                  id="edit-status"
                  defaultValue={selectedUser?.is_active ? 'active' : 'inactive'}
                >
                  <option value="active">Активен</option>
                  <option value="inactive">Неактивен</option>
                </select>
              </div>
            </div>
            
            <div className="modal-actions">
              <button
                onClick={() => handleSaveUser(selectedUser)}
                className="save-button"
              >
                Сохранить изменения
              </button>
              <button
                onClick={() => setShowEditModal(false)}
                className="cancel-button"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;