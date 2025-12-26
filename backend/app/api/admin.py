from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app import schemas, models
from app.database import get_db
from app.auth import get_current_active_admin
from app.rag.parser import WebParser
from app.rag.chroma_manager import ChromaManager

router = APIRouter()

@router.post("/parse-venues")
async def parse_venues(
    parser_config: schemas.ParserConfig,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
    chroma_manager: ChromaManager = Depends(lambda: ChromaManager())
):
    """
    Запускает фоновый процесс парсинга заведений (рестораны, бары и т.д.)
    с картографического сервиса по заданным параметрам.
    
    Args:
        parser_config: Конфигурация парсинга (город, категория, количество)
        background_tasks: Фоновые задачи FastAPI для асинхронной обработки
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
        chroma_manager: Менеджер векторной базы данных для хранения embeddings
    
    Returns:
        dict: Сообщение о запуске фоновой задачи
    """
    print("Тест парсинга")
    
    async def parse_task():
        """Фоновая задача парсинга и сохранения данных"""
        parser = WebParser(headless=True)
        try:
            print("Парсинг начат")
            venues = parser.parse_ymaps(
                city=parser_config.city,
                category=parser_config.category,
                items=parser_config.max_items
            )
            
            # Добавление в ChromaDB для векторного поиска
            chroma_manager.add_venues(venues)
            
            # Сохранение в реляционную базу данных
            for venue_data in venues:
                venue = models.Venue(
                    external_id=venue_data.get("external_id"),
                    name=venue_data.get("name"),
                    category=venue_data.get("category"),
                    description=venue_data.get("description"),
                    location=venue_data.get("location"),
                    price_range=venue_data.get("price_range"),
                    amenities=venue_data.get("amenities", []),
                    parsed_data=venue_data,
                    is_verified=False
                )
                db.add(venue)
            
            db.commit()
            
        finally:
            print("Завершение парсинга")
            # parser.close()
    
    background_tasks.add_task(parse_task)
    
    return {"message": "Парсинг запущен в фоновом режиме"}

@router.get("/unmoderated-ratings")
def get_unmoderated_ratings(
    limit: int = 50,
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Получает список непромодерированных отзывов для административной проверки.
    
    Args:
        limit: Максимальное количество возвращаемых отзывов (по умолчанию 50)
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
    
    Returns:
        List[VenueRating]: Список непромодерированных отзывов
    """
    ratings = db.query(models.VenueRating).filter(
        models.VenueRating.is_moderated == False
    ).order_by(models.VenueRating.created_at).limit(limit).all()
    
    return ratings

@router.post("/moderate-rating/{rating_id}")
def moderate_rating(
    rating_id: int,
    approve: bool = True,
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Модерация отзыва: одобрение или удаление.
    
    Args:
        rating_id: ID отзыва для модерации
        approve: Флаг одобрения (True - одобрить, False - удалить)
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
    
    Returns:
        dict: Результат модерации
    
    Raises:
        HTTPException: Если отзыв не найден
    """
    rating = db.query(models.VenueRating).filter(models.VenueRating.id == rating_id).first()
    
    if not rating:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    if approve:
        rating.is_moderated = True
    else:
        db.delete(rating)
    
    db.commit()
    
    return {"message": "Отзыв успешно промодерирован"}

@router.get("/users")
def get_users(
    role: str = None,
    is_active: bool = None,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Получает список пользователей с возможностью фильтрации по роли и активности.
    
    Args:
        role: Фильтр по роли пользователя (опционально)
        is_active: Фильтр по активности пользователя (опционально)
        limit: Максимальное количество возвращаемых пользователей
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
    
    Returns:
        List[User]: Список пользователей
    """
    query = db.query(models.User)
    
    if role:
        query = query.filter(models.User.role == role)
    
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    
    return query.limit(limit).all()

@router.post("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Активация/деактивация учетной записи пользователя.
    
    Args:
        user_id: ID пользователя
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
    
    Returns:
        dict: Статус операции
    
    Raises:
        HTTPException: Если пользователь не найден
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.is_active = not user.is_active
    db.commit()
    
    return {"message": f"Пользователь {'активирован' if user.is_active else 'деактивирован'}"}

@router.get("/stats")
def get_system_stats(
    current_user: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Получает статистику системы (количество пользователей, заведений, чатов и отзывов).
    
    Args:
        current_user: Текущий аутентифицированный администратор
        db: Сессия базы данных
    
    Returns:
        dict: Статистические показатели системы
    """
    from sqlalchemy import func
    
    stats = {
        "total_users": db.query(func.count(models.User.id)).scalar(),
        "total_venues": db.query(func.count(models.Venue.id)).scalar(),
        "total_chats": db.query(func.count(models.ChatHistory.id)).scalar(),
        "total_ratings": db.query(func.count(models.VenueRating.id)).scalar(),
        "active_users_24h": 0,  # Требует реализации отслеживания временных меток
    }
    
    return stats