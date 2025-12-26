import React from 'react';
import Rating from '../Common/Rating';
import './VenueCard.css';

const VenueCard = ({ venue, onSelect }) => {
  return (
    <div className="venue-card" onClick={() => onSelect(venue.id)}>
      <div className="venue-header">
        <h4 className="venue-name">{venue.name}</h4>
        {venue.category && (
          <span className="venue-category">{venue.category}</span>
        )}
      </div>
      
      {venue.score && (
        <div className="venue-score">
          <span className="score-label">Релевантность:</span>
          <div className="score-bar">
            <div 
              className="score-fill" 
              style={{ width: `${venue.score * 100}%` }}
            />
          </div>
          <span className="score-value">{Math.round(venue.score * 100)}%</span>
        </div>
      )}
      
      <div className="venue-actions">
        <button className="view-details-button">
          View Details
        </button>
      </div>
    </div>
  );
};

export default VenueCard;