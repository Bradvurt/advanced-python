from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app import schemas, models
from app.database import get_db
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user
)
from app.llm.chains import RecommendationChain
from app.llm.moderation import LlamaGuardModerator
from app.rag.chroma_manager import ChromaManager
from app.utils.clickhouse_client import ClickHouseMetrics
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя в системе.
    
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
    Аутентификация пользователя и выдача JWT токена.
    
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
    Обновление предпочтений пользователя (например, кулинарные предпочтения, бюджет и т.д.).
    
    Args:
        user_update: Новые данные пользователя
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

@router.post("/message", response_model=schemas.ChatResponse)
async def send_message(
    chat_message: schemas.ChatMessage,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clickhouse: ClickHouseMetrics = Depends(lambda: ClickHouseMetrics())
):
    """
    Обработка сообщения пользователя и получение ответа от чатбота с рекомендациями.
    
    Процесс:
    1. Генерация или использование существующего session_id
    2. Проверка безопасности запроса через модерацию
    3. Получение рекомендаций через LLM цепочку
    4. Логирование взаимодействия
    
    Args:
        chat_message: Сообщение от пользователя
        background_tasks: Фоновые задачи для асинхронной обработки
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
        clickhouse: Клиент для логирования метрик
    
    Returns:
        ChatResponse: Ответ от чатбота с рекомендациями
    """
    # Генерация ID сессии, если не предоставлен
    session_id = chat_message.session_id or str(uuid.uuid4())
    
    # Модерация запроса на безопасность
    moderator = LlamaGuardModerator()
    is_safe = await moderator.execute_query(chat_message.message)
    
    if not is_safe:
        # Логирование небезопасного запроса
        background_tasks.add_task(
            clickhouse.log_interaction,
            current_user.id,
            session_id,
            "unsafe_query",
            {"query": chat_message.message[:100]}  # Обрезаем для безопасности
        )
        
        return schemas.ChatResponse(
            response="Я не могу обработать этот запрос, так как он нарушает политики безопасности контента.",
            session_id=session_id,
            is_safe=False
        )

    llm_cache = CustomSemanticCache()
    cached_response = llm_cache.check(prompt=chat_message.message)
    result = ""
    if cached_response:
        print("Cache Hit!")
        print("Prompt:", cached_response[0]['prompt'])
        print("Response:", cached_response[0]['response'])
        result = cached_response
    else:
        print("Cache Missed!")
        recommender = RecommendationChain()
        print("PREFERENCES:",current_user.preferences or {})
        result = await recommender.async_execute_query(
            query=chat_message.message,
            user_preferences=current_user.preferences or {}
        )
        print("RESULT", result)
        
        # Кеширование
        llm_cache.store(prompt=chat_message.message, response=result)
        #print("Кеширование успешно.")
    
    # Логирование взаимодействия
    background_tasks.add_task(
        clickhouse.log_interaction,
        current_user.id,
        session_id,
        "chat_message",
        {"query_length": len(chat_message.message), "response_length": len(result)}
    )
    
    return schemas.ChatResponse(
        response=result,
        session_id=session_id,
        venues=[],
        is_safe=is_safe
    )

@router.get("/history", response_model=list[schemas.ChatHistoryResponse])
def get_chat_history(
    session_id: str = None,
    limit: int = 50,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение истории чата для текущего пользователя.
    
    Args:
        session_id: ID конкретной сессии (опционально)
        limit: Максимальное количество сообщений для возврата
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
    
    Returns:
        List[ChatHistoryResponse]: История сообщений чата
    """
    query = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == current_user.id
    ).order_by(models.ChatHistory.created_at.desc())
    
    if session_id:
        query = query.filter(models.ChatHistory.session_id == session_id)
    
    return query.limit(limit).all()

@router.post("/rate-answer")
def rate_answer(
    rating_data: schemas.AnswerRatingCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    clickhouse: ClickHouseMetrics = Depends(lambda: ClickHouseMetrics())
):
    """
    Оценка ответа от чатбота пользователем.
    
    Args:
        rating_data: Данные оценки (ID чата, рейтинг, отзыв)
        current_user: Текущий аутентифицированный пользователь
        db: Сессия базы данных
        clickhouse: Клиент для логирования метрик
    
    Returns:
        dict: Результат сохранения оценки
    
    Raises:
        HTTPException: Если чат не найден или не принадлежит пользователю
    """
    # Проверка существования чата и принадлежности пользователю
    chat = db.query(models.ChatHistory).filter(
        models.ChatHistory.id == rating_data.chat_id,
        models.ChatHistory.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    # Создание или обновление оценки
    existing_rating = db.query(models.AnswerRating).filter(
        models.AnswerRating.user_id == current_user.id,
        models.AnswerRating.chat_id == rating_data.chat_id
    ).first()
    
    if existing_rating:
        existing_rating.rating = rating_data.rating
        existing_rating.feedback = rating_data.feedback
    else:
        rating = models.AnswerRating(
            user_id=current_user.id,
            chat_id=rating_data.chat_id,
            rating=rating_data.rating,
            feedback=rating_data.feedback
        )
        db.add(rating)
    
    db.commit()
    
    # Логирование оценки
    clickhouse.log_interaction(
        current_user.id,
        chat.session_id,
        "answer_rating",
        {"rating": rating_data.rating, "feedback_length": len(rating_data.feedback or "")}
    )
    
    return {"message": "Оценка успешно сохранена"}