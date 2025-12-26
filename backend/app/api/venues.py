from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app import schemas, models
from app.database import get_db
from app.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[schemas.VenueResponse])
def get_venues(
    category: Optional[str] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    price_range: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Получение списка заведений с возможностью фильтрации.
    
    Args:
        category: Категория заведения (например, "ресторан", "кофейня")
        min_rating: Минимальный рейтинг заведения (от 0 до 5)
        price_range: Ценовой диапазон (например, "$", "$$", "$$$")
        limit: Количество заведений на странице
        offset: Смещение для пагинации
        db: Сессия базы данных
    
    Returns:
        List[VenueResponse]: Список заведений, отсортированный по рейтингу
    """
    query = db.query(models.Venue).filter(models.Venue.is_verified == True)
    
    if category:
        query = query.filter(models.Venue.category.ilike(f"%{category}%"))
    
    if min_rating is not None:
        query = query.filter(models.Venue.rating >= min_rating)
    
    if price_range:
        query = query.filter(models.Venue.price_range == price_range)
    
    return query.order_by(models.Venue.rating.desc()).offset(offset).limit(limit).all()

@router.get("/{venue_id}", response_model=schemas.VenueResponse)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """
    Получение детальной информации о конкретном заведении.
    
    Args:
        venue_id: ID заведения
        db: Сессия базы данных
    
    Returns:
        VenueResponse: Полная информация о заведении
    
    Raises:
        HTTPException: Если заведение не найдено
    """
    venue = db.query(models.Venue).filter(models.Venue.id == venue_id).first()
    
    if not venue:
        raise HTTPException(status_code=404, detail="Заведение не найдено")
    
    return venue

@router.post("/{venue_id}/rate")
def rate_venue(
    venue_id: int,
    rating_data: schemas.VenueRatingCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Оценка заведения пользователем и обновление его среднего рейтинга.
    
    Args:
        venue_id: ID заведения для оценки
        rating_data: Данные оценки (рейтинг, отзыв)
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
    
    Returns:
        dict: Сообщение об успешном сохранении и новый средний рейтинг
    
    Raises:
        HTTPException: Если заведение не найдено
    """
    # Проверка существования заведения
    venue = db.query(models.Venue).filter(models.Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Заведение не найдено")
    
    # Проверка, оценивал ли пользователь это заведение ранее
    existing_rating = db.query(models.VenueRating).filter(
        models.VenueRating.user_id == current_user.id,
        models.VenueRating.venue_id == venue_id
    ).first()
    
    if existing_rating:
        existing_rating.rating = rating_data.rating
        existing_rating.review = rating_data.review
    else:
        rating = models.VenueRating(
            user_id=current_user.id,
            venue_id=venue_id,
            rating=rating_data.rating,
            review=rating_data.review
        )
        db.add(rating)
    
    # Обновление среднего рейтинга заведения
    ratings_query = db.query(
        func.avg(models.VenueRating.rating).label('avg_rating'),
        func.count(models.VenueRating.id).label('count')
    ).filter(models.VenueRating.venue_id == venue_id)
    
    result = ratings_query.first()
    venue.rating = result.avg_rating or 0
    venue.review_count = result.count or 0
    
    db.commit()
    
    return {"message": "Оценка успешно сохранена", "new_average": venue.rating}

@router.get("/{venue_id}/reviews")
def get_venue_reviews(
    venue_id: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Получение отзывов о заведении (только промодерированные).
    
    Args:
        venue_id: ID заведения
        limit: Количество отзывов на странице
        offset: Смещение для пагинации
        db: Сессия базы данных
    
    Returns:
        List[VenueRating]: Список отзывов, отсортированный по дате (сначала новые)
    """
    reviews = db.query(models.VenueRating).filter(
        models.VenueRating.venue_id == venue_id,
        models.VenueRating.is_moderated == True
    ).order_by(models.VenueRating.created_at.desc()).offset(offset).limit(limit).all()
    
    return reviews