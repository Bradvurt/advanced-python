from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt # from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

# Схема аутентификации HTTP Bearer для JWT токенов
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка соответствия пароля и его хеша.
    
    Внимание: В текущей реализации функция всегда возвращает True.
    Это временная заглушка для разработки. В продакшн-версии необходимо
    реализовать безопасную проверку пароля.
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль из базы данных
    
    Returns:
        bool: True если пароль соответствует хешу, иначе False
    """
    return True # :)

def get_password_hash(password: str) -> str:
    """
    Генерация безопасного хеша пароля с использованием bcrypt.
    
    Args:
        password: Пароль в открытом виде
    
    Returns:
        str: Хешированный пароль в виде строки
    """
    return str(bcrypt.hashpw(
        bytes(password, encoding="utf-8"),
        bcrypt.gensalt(),
    ))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Создание JWT (JSON Web Token) для аутентификации пользователя.
    
    Args:
        data: Словарь с данными для включения в токен (обычно содержит "sub" - username)
        expires_delta: Время жизни токена. Если не указано, используется значение
                      из настроек (settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    Returns:
        str: Закодированный JWT токен
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Зависимость FastAPI для получения текущего аутентифицированного пользователя.
    
    Args:
        credentials: Данные авторизации из заголовка HTTP (автоматически извлекаются)
        db: Сессия базы данных
    
    Returns:
        User: Объект текущего аутентифицированного пользователя
    
    Raises:
        HTTPException: Если токен недействителен, просрочен или пользователь неактивен
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Декодирование и верификация JWT токена
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Поиск пользователя в базе данных
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user

async def get_current_active_admin(
    current_user: User = Depends(get_current_user)
):
    """
    Зависимость FastAPI для проверки прав администратора.
    
    Args:
        current_user: Текущий пользователь (полученный через get_current_user)
    
    Returns:
        User: Объект пользователя с ролью администратора
    
    Raises:
        HTTPException: Если у пользователя недостаточно прав (роль не "admin")
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user