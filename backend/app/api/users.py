from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta

from app import schemas, models
from app.database import get_db
from app.auth import (
    verify_password, get_password_hash, create_access_token,
)
from app.auth import get_current_user, get_current_active_admin
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя.
    
    Args:
        user_data: Данные для регистрации (имя пользователя, email, пароль)
        db: Сессия базы данных
    
    Returns:
        UserResponse: Зарегистрированный пользователь
    
    Raises:
        HTTPException: Если пользователь с таким именем или email уже существует
    """
    # Проверка существования пользователя
    existing_user = db.query(models.User).filter(
        (models.User.username == user_data.username) | 
        (models.User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким именем или email уже существует"
        )
    
    # Создание нового пользователя
    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        preferences={}
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=schemas.Token)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Аутентификация пользователя и получение JWT токена.
    
    Args:
        login_data: Данные для входа (имя пользователя, пароль)
        db: Сессия базы данных
    
    Returns:
        Token: JWT токен доступа
    
    Raises:
        HTTPException: Если неверные учетные данные или пользователь неактивен
    """
    user = db.query(models.User).filter(models.User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Пользователь неактивен"
        )
    
    # Создание токена доступа
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """
    Получение информации о текущем аутентифицированном пользователе.
    
    Args:
        current_user: Текущий аутентифицированный пользователь
    
    Returns:
        UserResponse: Информация о пользователе
    """
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
def update_user_preferences(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновление предпочтений пользователя.
    
    Args:
        user_update: Новые данные пользователя (включая предпочтения)
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
    
    Returns:
        UserResponse: Обновленная информация о пользователе
    """
    if user_update.preferences is not None:
        current_user.preferences = user_update.preferences
        db.commit()
        db.refresh(current_user)
    
    return current_user

@router.get("/me/preferences", response_model=dict)
def get_user_preferences(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение предпочтений текущего пользователя.
    
    Args:
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
    
    Returns:
        dict: Словарь с предпочтениями пользователя
    """
    return current_user.preferences or {}

@router.put("/me/preferences", response_model=dict)
def update_user_preferences(
    preferences: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновление предпочтений текущего пользователя.
    
    Args:
        preferences: Новые предпочтения в формате словаря
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
    
    Returns:
        dict: Обновленные предпочтения пользователя
    """
    current_user.preferences = preferences
    db.commit()
    db.refresh(current_user)
    return current_user.preferences

@router.get("/me/history", response_model=List[schemas.ChatHistoryResponse])
def get_user_chat_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение истории чатов текущего пользователя с пагинацией.
    
    Args:
        limit: Количество записей на странице (1-100)
        offset: Смещение для пагинации
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
    
    Returns:
        List[ChatHistoryResponse]: История чатов пользователя
    """
    history = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == current_user.id
    ).order_by(
        models.ChatHistory.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return history

@router.get("/me/ratings", response_model=List[dict])
def get_user_ratings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение оценок заведений, оставленных текущим пользователем.
    
    Args:
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
    
    Returns:
        List[dict]: Список оценок пользователя
    """
    ratings = db.query(models.VenueRating).filter(
        models.VenueRating.user_id == current_user.id
    ).all()
    
    return [
        {
            "id": rating.id,
            "venue_id": rating.venue_id,
            "venue_name": rating.venue.name if rating.venue else "Неизвестно",
            "rating": rating.rating,
            "review": rating.review,
            "created_at": rating.created_at,
            "is_moderated": rating.is_moderated
        }
        for rating in ratings
    ]

@router.get("/me/stats", response_model=dict)
def get_user_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение статистики активности текущего пользователя.
    
    Args:
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
    
    Returns:
        dict: Статистика пользователя (чаты, оценки, активность)
    """
    from sqlalchemy import func
    
    # Количество чатов
    chat_count = db.query(func.count(models.ChatHistory.id)).filter(
        models.ChatHistory.user_id == current_user.id
    ).scalar()
    
    # Количество оценок заведений
    ratings_count = db.query(func.count(models.VenueRating.id)).filter(
        models.VenueRating.user_id == current_user.id
    ).scalar()
    
    # Количество оценок ответов
    answer_ratings_count = db.query(func.count(models.AnswerRating.id)).filter(
        models.AnswerRating.user_id == current_user.id
    ).scalar()
    
    # Средняя оценка ответов
    avg_answer_rating = db.query(func.avg(models.AnswerRating.rating)).filter(
        models.AnswerRating.user_id == current_user.id
    ).scalar() or 0
    
    # Дата первой активности
    first_chat = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == current_user.id
    ).order_by(models.ChatHistory.created_at).first()
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "chat_count": chat_count,
        "ratings_count": ratings_count,
        "answer_ratings_count": answer_ratings_count,
        "avg_answer_rating": float(avg_answer_rating),
        "first_activity": first_chat.created_at if first_chat else current_user.created_at,
        "account_created": current_user.created_at
    }

@router.get("/search", response_model=List[schemas.UserResponse])
def search_users(
    query: Optional[str] = Query(None, description="Поиск по имени пользователя или email"),
    role: Optional[str] = Query(None, description="Фильтр по роли"),
    is_active: Optional[bool] = Query(None, description="Фильтр по статусу активности"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Поиск пользователей (только для администраторов).
    
    Args:
        query: Поисковый запрос по имени пользователя или email
        role: Фильтрация по роли пользователя
        is_active: Фильтрация по статусу активности
        limit: Количество записей на странице
        offset: Смещение для пагинации
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
    
    Returns:
        List[UserResponse]: Список пользователей, соответствующих критериям
    """
    from sqlalchemy import or_
    
    q = db.query(models.User)
    
    if query:
        q = q.filter(
            or_(
                models.User.username.ilike(f"%{query}%"),
                models.User.email.ilike(f"%{query}%")
            )
        )
    
    if role:
        q = q.filter(models.User.role == role)
    
    if is_active is not None:
        q = q.filter(models.User.is_active == is_active)
    
    return q.order_by(models.User.created_at.desc()).offset(offset).limit(limit).all()

@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Получение информации о пользователе по ID (только для администраторов).
    
    Args:
        user_id: ID пользователя
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
    
    Returns:
        UserResponse: Информация о пользователе
    
    Raises:
        HTTPException: Если пользователь не найден
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user

@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Обновление информации о пользователе (только для администраторов).
    
    Args:
        user_id: ID пользователя для обновления
        user_update: Новые данные пользователя
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
    
    Returns:
        UserResponse: Обновленная информация о пользователе
    
    Raises:
        HTTPException: Если пользователь не найден
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Обновление полей пользователя
    if user_update.preferences is not None:
        user.preferences = user_update.preferences
    
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Удаление пользователя (только для администраторов) - мягкое удаление через деактивацию.
    
    Args:
        user_id: ID пользователя для удаления
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
    
    Returns:
        dict: Результат операции
    
    Raises:
        HTTPException: Если пользователь не найден или попытка удалить свой аккаунт
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить свой собственный аккаунт")
    
    # Мягкое удаление через деактивацию
    user.is_active = False
    db.commit()
    
    return {"message": "Пользователь успешно деактивирован"}