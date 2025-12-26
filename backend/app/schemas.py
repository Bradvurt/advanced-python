from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Chat schemas
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    venues: Optional[List[Dict[str, Any]]] = None
    is_safe: bool = True

class ChatHistoryResponse(BaseModel):
    id: int
    message: str
    response: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Venue schemas
class VenueBase(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    price_range: Optional[str] = None
    amenities: Optional[List[str]] = None

class VenueCreate(VenueBase):
    external_id: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None

class VenueResponse(VenueBase):
    id: int
    rating: float
    review_count: int
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class VenueRatingCreate(BaseModel):
    venue_id: int
    rating: float
    review: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 0 or v > 5:
            raise ValueError('Рейтинг должен быть между 1 и 5')
        return v

class AnswerRatingCreate(BaseModel):
    chat_id: int
    rating: int
    feedback: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Рейтинг должен быть между 1 и 5')
        return v

# Admin schemas
class ParserConfig(BaseModel):
    city: str
    category: str
    max_items: Optional[int] = 100

# User schemas
class UserUpdate(BaseModel):
    preferences: Optional[Dict[str, Any]] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v and v not in ['user', 'admin']:
            raise ValueError('Роль должна быть "user" или "admin"')
        return v