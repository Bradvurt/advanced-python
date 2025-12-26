import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { userAPI } from '../../services/api';
import './Preferences.css';

const PreferencesForm = () => {
  const { user, updatePreferences } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    categories: [],
    priceRange: '$$',
    location: '',
    amenities: [],
    preferredTimes: [],
    groupSize: '2-4',
    dietaryRestrictions: [],
    accessibilityNeeds: [],
  });

  const categories = [
    'Рестораны', 'Бары', 'Кофейни', 'Парки', 'Музеи',
    'Театры', 'Живая музыка', 'Спорт', 'Шопинг', 'Ночная жизнь'
  ];

  const amenitiesList = [
    'WiFi', 'Уличные столики', 'Парковка', 'Доступно для инвалидных колясок',
    'Вегетарианские блюда', 'Алкоголь', 'Для семей', 'Разрешено с животными',
    'Бронирование', 'Доставка', 'На вынос'
  ];

  const times = ['Утро', 'День', 'Вечер', 'Поздняя ночь'];

  const dietaryRestrictions = [
    'Вегетарианская', 'Веганская', 'Без глютена', 'Без молочных', 'Кошерная', 'Халяль'
  ];

  const accessibilityOptions = [
    'Доступно для инвалидных колясок', 'Лифт', 'Пандус', 'Доступные туалеты',
    'Меню Брайля', 'Персонал жестового языка'
  ];

  useEffect(() => {
    if (user?.preferences) {
      setFormData(prev => ({
        ...prev,
        ...user.preferences
      }));
    }
  }, [user]);

  const handleCategoryToggle = (category) => {
    setFormData(prev => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter(c => c !== category)
        : [...prev.categories, category]
    }));
  };

  const handleAmenityToggle = (amenity) => {
    setFormData(prev => ({
      ...prev,
      amenities: prev.amenities.includes(amenity)
        ? prev.amenities.filter(a => a !== amenity)
        : [...prev.amenities, amenity]
    }));
  };

  const handleTimeToggle = (time) => {
    setFormData(prev => ({
      ...prev,
      preferredTimes: prev.preferredTimes.includes(time)
        ? prev.preferredTimes.filter(t => t !== time)
        : [...prev.preferredTimes, time]
    }));
  };

  const handleDietaryToggle = (restriction) => {
    setFormData(prev => ({
      ...prev,
      dietaryRestrictions: prev.dietaryRestrictions.includes(restriction)
        ? prev.dietaryRestrictions.filter(d => d !== restriction)
        : [...prev.dietaryRestrictions, restriction]
    }));
  };

  const handleAccessibilityToggle = (option) => {
    setFormData(prev => ({
      ...prev,
      accessibilityNeeds: prev.accessibilityNeeds.includes(option)
        ? prev.accessibilityNeeds.filter(a => a !== option)
        : [...prev.accessibilityNeeds, option]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await userAPI.updatePreferences(formData);
      updatePreferences(formData);
      navigate('/chat');
    } catch (error) {
      console.error('Не удалось сохранить настройки:', error);
      alert('Не удалось сохранить настройки. Пожалуйста, попробуйте снова.');
    }
  };

  const handleSkip = () => {
    navigate('/chat');
  };

  const handleReset = () => {
    setFormData({
      categories: [],
      priceRange: '$$',
      location: '',
      amenities: [],
      preferredTimes: [],
      groupSize: '2-4',
      dietaryRestrictions: [],
      accessibilityNeeds: [],
    });
  };

  return (
    <div className="preferences-container">
      <div className="preferences-card">
        <h2 className="preferences-title">Расскажите о своих предпочтениях</h2>
        <p className="preferences-subtitle">
          Помогите нам давать лучшие рекомендации, поделившись своими предпочтениями
        </p>

        <form onSubmit={handleSubmit} className="preferences-form">
          {/* Категории */}
          <div className="preferences-section">
            <h3>Какие места вам нравятся? (Выберите все подходящие)</h3>
            <div className="preferences-grid">
              {categories.map(category => (
                <button
                  key={category}
                  type="button"
                  className={`preference-chip ${
                    formData.categories.includes(category) ? 'active' : ''
                  }`}
                  onClick={() => handleCategoryToggle(category)}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          {/* Ценовой диапазон */}
          <div className="preferences-section">
            <h3>Предпочитаемый ценовой диапазон</h3>
            <div className="price-range">
              {['$', '$$', '$$$', '$$$$'].map(range => (
                <button
                  key={range}
                  type="button"
                  className={`price-option ${
                    formData.priceRange === range ? 'active' : ''
                  }`}
                  onClick={() => setFormData(prev => ({ ...prev, priceRange: range }))}
                >
                  {range}
                </button>
              ))}
            </div>
            <p className="price-description">
              $ = Бюджет, $$ = Средний, $$$ = Дорого, $$$$ = Роскошь
            </p>
          </div>

          {/* Удобства */}
          <div className="preferences-section">
            <h3>Важные удобства (Выберите все подходящие)</h3>
            <div className="preferences-grid">
              {amenitiesList.map(amenity => (
                <button
                  key={amenity}
                  type="button"
                  className={`preference-chip ${
                    formData.amenities.includes(amenity) ? 'active' : ''
                  }`}
                  onClick={() => handleAmenityToggle(amenity)}
                >
                  {amenity}
                </button>
              ))}
            </div>
          </div>

          {/* Предпочитаемое время посещения */}
          <div className="preferences-section">
            <h3>Предпочитаемое время посещения (Выберите все подходящие)</h3>
            <div className="preferences-grid">
              {times.map(time => (
                <button
                  key={time}
                  type="button"
                  className={`preference-chip ${
                    formData.preferredTimes.includes(time) ? 'active' : ''
                  }`}
                  onClick={() => handleTimeToggle(time)}
                >
                  {time}
                </button>
              ))}
            </div>
          </div>

          {/* Размер группы */}
          <div className="preferences-section">
            <h3>Размер группы</h3>
            <div className="group-size">
              {['Один', '2-4', '5-8', '9+'].map(size => (
                <button
                  key={size}
                  type="button"
                  className={`group-option ${
                    formData.groupSize === size ? 'active' : ''
                  }`}
                  onClick={() => setFormData(prev => ({ ...prev, groupSize: size }))}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>

          {/* Локация */}
          <div className="preferences-section">
            <h3>Предпочитаемый район/место</h3>
            <input
              type="text"
              className="location-input"
              placeholder="Например: центр города, западная часть и т.д."
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
            />
          </div>

          {/* Диетические ограничения */}
          <div className="preferences-section">
            <h3>Диетические ограничения (по желанию)</h3>
            <div className="preferences-grid">
              {dietaryRestrictions.map(restriction => (
                <button
                  key={restriction}
                  type="button"
                  className={`preference-chip ${
                    formData.dietaryRestrictions.includes(restriction) ? 'active' : ''
                  }`}
                  onClick={() => handleDietaryToggle(restriction)}
                >
                  {restriction}
                </button>
              ))}
            </div>
          </div>

          {/* Потребности в доступности */}
          <div className="preferences-section">
            <h3>Потребности в доступности (по желанию)</h3>
            <div className="preferences-grid">
              {accessibilityOptions.map(option => (
                <button
                  key={option}
                  type="button"
                  className={`preference-chip ${
                    formData.accessibilityNeeds.includes(option) ? 'active' : ''
                  }`}
                  onClick={() => handleAccessibilityToggle(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          {/* Дополнительные предпочтения */}
          <div className="preferences-section">
            <h3>Дополнительные предпочтения</h3>
            <div className="additional-preferences">
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.prefersQuiet || false}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      prefersQuiet: e.target.checked 
                    }))}
                  />
                  <span>Предпочитаю тихие места</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.prefersDateNight || false}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      prefersDateNight: e.target.checked 
                    }))}
                  />
                  <span>Подходит для свиданий</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.prefersFamily || false}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      prefersFamily: e.target.checked 
                    }))}
                  />
                  <span>Подходит для семей</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.prefersGroupEvents || false}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      prefersGroupEvents: e.target.checked 
                    }))}
                  />
                  <span>Подходит для групповых мероприятий</span>
                </label>
              </div>
            </div>
          </div>

          <div className="preferences-actions">
            <button
              type="button"
              className="reset-button"
              onClick={handleReset}
            >
              Сбросить все
            </button>
            <button
              type="button"
              className="skip-button"
              onClick={handleSkip}
            >
              Пропустить
            </button>
            <button
              type="submit"
              className="save-button"
            >
              Сохранить настройки
            </button>
          </div>
        </form>

        <div className="preferences-note">
          <p>💡 Вы всегда можете обновить эти настройки позже в профиле.</p>
        </div>
      </div>
    </div>
  );
};

export default PreferencesForm;