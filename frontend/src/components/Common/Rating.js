import React from 'react';
import './Rating.css';

const Rating = ({ value, onChange, readOnly = false, max = 5 }) => {
  const stars = Array.from({ length: max }, (_, i) => i + 1);

  const handleClick = (starValue) => {
    if (!readOnly && onChange) {
      onChange(starValue);
    }
  };

  return (
    <div className="rating">
      {stars.map((star) => (
        <button
          key={star}
          type="button"
          className={`star ${star <= value ? 'filled' : ''} ${readOnly ? 'readonly' : ''}`}
          onClick={() => handleClick(star)}
          disabled={readOnly}
          aria-label={`Rate ${star} out of ${max}`}
        >
          ★
        </button>
      ))}
    </div>
  );
};

export default Rating;