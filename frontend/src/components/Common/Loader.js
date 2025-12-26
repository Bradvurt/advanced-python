import React from 'react';
import './Loader.css';

const Loader = ({ size = 'medium', color = '#2563eb' }) => {
  const loaderClass = `loader loader-${size}`;
  
  return (
    <div className={loaderClass}>
      <div className="spinner" style={{ borderColor: color }}></div>
    </div>
  );
};

export default Loader;