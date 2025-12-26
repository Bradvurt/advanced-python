import React, { useState } from 'react';
import { adminAPI } from '../../services/api';
import './ParserControl.css';

const ParserControl = () => {
  const [parserConfig, setParserConfig] = useState({
    city: 'Москва',
    category: 'restaurants',
    max_items: 10,
  });
  const [parsing, setParsing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  /*
  const categories = [
    'restaurants', 'bars', 'coffee', 'parks', 'museums',
    'theaters', 'music', 'sports', 'shopping', 'nightlife'
  ];
  */

  const categories = [
    'Ресторан', 'Бар', 'Кофейня', 'Парк', 'Музей',
    'Театр', 'Опера', 'Стадион', 'Торговый центр', 'Клуб'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setParsing(true);
    setError('');
    setResult(null);

    try {
      const response = await adminAPI.parseVenues(parserConfig);
      setResult({
        message: 'Сбор данных запущен',
        details: 'Процесс выполняется в фоне. Результаты появятся позже'
      });
    } catch (error) {
      setError(error.response?.data?.detail || 'Не удалось запустить сбор данных');
    } finally {
      setParsing(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setParserConfig(prev => ({
      ...prev,
      [name]: name === 'max_items' ? parseInt(value) || 10 : value
    }));
  };

  return (
    <div className="parser-control">
      <h3>Управление парсером</h3>
      
      <form onSubmit={handleSubmit} className="parser-form">
        <div className="form-group">
          <label htmlFor="city">Город</label>
          <input
            type="text"
            id="city"
            name="city"
            value={parserConfig.city}
            onChange={handleChange}
            placeholder="Москва, Санкт-Петербург..."
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="category">Категория</label>
          <select
            id="category"
            name="category"
            value={parserConfig.category}
            onChange={handleChange}
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="max_items">Максимальное количество</label>
          <input
            type="number"
            id="max_items"
            name="max_items"
            value={parserConfig.max_items}
            onChange={handleChange}
            min="1"
            max="100"
          />
        </div>

        <button
          type="submit"
          className="parse-button"
          disabled={parsing}
        >
          {parsing ? 'Идёт сбор данных...' : 'Запустить сбор данных'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {result && (
        <div className="result-message">
          <h4>{result.message}</h4>
          <p>{result.details}</p>
        </div>
      )}

      <div className="parser-info">
        <h4>Parser Information</h4>
        <ul>
          <li>На данный момент поддерживается только Яндекс.Карты</li>
          <li>Собираемые данные: название, рейтинг, ценовой уровень, категория, адрес, удобства</li>
          <li>Данные сохраняются в векторной базе ChromaDB</li>
          <li>Сбор данных выполняется в фоновом режиме</li>
        </ul>
      </div>
    </div>
  );
};

export default ParserControl;