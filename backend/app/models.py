from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.USER.value)
    preferences = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    venue_ratings = relationship("VenueRating", back_populates="user", cascade="all, delete-orphan")
    answer_ratings = relationship("AnswerRating", back_populates="user", cascade="all, delete-orphan")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    session_id = Column(String(100), index=True)
    message = Column(Text, nullable=False)
    response = Column(Text)
    is_moderated = Column(Boolean, default=True)
    #metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="chat_history")

class Venue(Base):
    __tablename__ = "venues"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    location = Column(JSON)
    price_range = Column(String(20))
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    amenities = Column(JSON, default=[])
    parsed_data = Column(JSON, default={})
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    ratings = relationship("VenueRating", back_populates="venue", cascade="all, delete-orphan")

class VenueRating(Base):
    __tablename__ = "venue_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"))
    rating = Column(Float, nullable=False)
    review = Column(Text)
    is_moderated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="venue_ratings")
    venue = relationship("Venue", back_populates="ratings")

class AnswerRating(Base):
    __tablename__ = "answer_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    chat_id = Column(Integer, ForeignKey("chat_history.id", ondelete="CASCADE"))
    rating = Column(Integer, nullable=False)  # 1-5
    feedback = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="answer_ratings")