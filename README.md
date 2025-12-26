# VenueBot

Система персонализированных рекомендаций развлекательных заведений и мест для отдыха с использованием LLM и RAG.

## **Основные возможности**

*   ** Чат с LLM**: Естественные диалоги для персонализированных рекомендаций с использованием LocalAI и LangChain.
*   ** RAG-система**: Рекомендации на основе наиболее актуальных данных
*   ** Управление пользователями**: Полная аутентификация (JWT), ролевой доступ (RBAC) и профили предпочтений.
*   ** Сбор данных**: Автоматический парсинг информации о заведениях из веб-источников с использованием Selenium.
*   ** UGC и модерация**: Возможность оценивать заведения и ответы ИИ с последующей модерацией отзывов администрацией
*   ** Оптимизация**: Кэширование Redis для запросов к LLM и семантического сопоставления.

## **Архитектура системы**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ React Frontend  │ ◄──►│  FastAPI Backend│ ◄──►│    AI/Data Layer│
│   (JavaScript)  │     │    (Python)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Chat Interface │     │  LangChain RAG  │     │   LocalAI LLM   │
│  Admin Dashboard│     │   ChromaDB      │     │   Embeddings    │
│   Venue Browser │     │   Redis Cache   │     │   Moderation    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

##  **Технологический стек**

*   **Backend**: FastAPI (Python 3.9+)
*   **LLM**: LocalAI (Qwen3 + Gemma3), LangChain (RetrievalQA)
*   **Базы данных**: SQLite + ChromaDB
*   **Кэширование**: RedisVL
*   **Веб-парсинг**: Selenium, BeautifulSoup
*   **Frontend**: Next.js 14 (React, JavaScript)

## **Быстрый старт**

### **Предварительные требования**
- Docker и Docker Compose
- Python 3.9+ (для локальной разработки)
- Node.js 18+ (для фронтенда)

### **1. Клонирование и настройка**
```bash
# Клонировать репозиторий
git clone <repository-url>
cd venue-recommendation-chatbot

# Скопировать шаблоны переменных окружения
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Обновить конфигурации (опционально)
# Отредактируйте backend/.env для API ключей и URL
# Отредактируйте frontend/.env для эндпоинта API
```

### **2. Запуск с Docker**
```bash
# Собрать и запустить все сервисы
docker-compose up -d --build

# Сервисы будут доступны по адресам:
# - Фронтенд: http://localhost:3000
# - Бэкенд API: http://localhost:8000
# - Документация API: http://localhost:8000/docs

# Запуск LocalAI, в UI загрузить Backend llama.cpp и модели llama-guard-3-8b, qwen3-embedding-4b, gemma-3-12b-it
docker run -p 8080:8080 --name local-ai -ti localai/localai:latest
```

### **3. Инициализация системы**
```bash
# Создать администратора по умолчанию
docker-compose exec backend python add_admin.py
```

### **4. Ручная установка (разработка)**
```bash
# Настройка бэкенда
cd backend
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Настройка фронтенда (в другом терминале)
cd frontend
npm install
npm start
```

## **Структура проекта**

```
venue-recommendation-chatbot/
├── backend/                 # FastAPI бэкенд
│   ├── app/
│   │   ├── api/            # API эндпоинты (chat, users, venues, admin)
│   │   ├── llm/            # LangChain цепи, модерация, кэширование
│   │   ├── rag/            # ChromaDB эмбеддинги, парсер Yandex.Maps
│   │   ├── models.py       # SQLAlchemy модели
│   │   ├── schemas.py      # Pydantic схемы
│   │   └── main.py         # FastAPI приложение
│   ├── scripts/            # Инициализация БД, примеры данных
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React фронтенд
│   ├── src/
│   │   ├── components/     # React компоненты (Auth, Chat, Admin и т.д.)
│   │   ├── context/        # React Context (Auth)
│   │   ├── services/       # API сервисный слой
│   │   ├── styles/         # CSS файлы
│   │   └── App.js          # Приложение
│   ├── public/
│   └── package.json
├── docker-compose.yml
└── README.md         
```

## **Конфигурация**

### **Переменные окружения**

**(`.env`):**
```env
# БД
DATABASE_URL: str = "sqlite:///./recommendations.db"

# JWT
SECRET_KEY: str = "your-secret-key-change-in-production"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

# Redis
REDIS_URL: str = "redis://redis:6379"

# LLM
LOCALAI_BASE_URL: str = "http://host.docker.internal:8080/v1"
LLM_MODEL: str = "gemma-3-12b-it"
MODERATION_MODEL: str = "llama-guard-3-8b"
EMBEDDING_MODEL: str = "qwen3-embedding-4b"
OPENAI_API_KEY: str = "sk-something"
OPENAI_API_BASE: str = "http://host.docker.internal:8080/v1"
MODEL_TYPE: str = "OpenAI"
MODEL_N_CTX: int = 1024
EMBEDDING_CTX_LENGTH: int = 8192

# ChromaDB
#CHROMA_HOST: str = "http://chromadb:8000"
CHROMA_PERSIST_DIR: str = "./chroma_db"

# ClickHouse
CLICKHOUSE_HOST: str = "localhost"
CLICKHOUSE_PORT: int = 9000
CLICKHOUSE_USER: str = "default"
CLICKHOUSE_PASSWORD: str = "default"
CLICKHOUSE_DATABASE: str = "default"
```

### **Порты сервисов**
| Сервис | Порт | Описание |
|---------|------|-------------|
| Фронтенд | 3000 | React development server |
| Бэкенд API | 8000 | FastAPI приложение |
| Документация API | 8000/docs | Интерактивная документация |
| LocalAI | 8080 | LLM и эмбеддинги |
| Redis | 6379 | Кэширование и сессии |
| ClickHouse | 9000 | Аналитическая база данных |

## **Руководство по использованию**

### **Для конечных пользователей**
1. **Регистрация/Вход**: Создать аккаунт или использовать тестовые данные
2. **Настройка предпочтений**: Указать категории заведений, ценовые диапазоны, удобства
3. **Начать общение**: Задавать вопросы на естественном языке о заведениях
4. **Исследовать и оценивать**: Просматривать детали заведений, оценивать их и ответы ИИ

### **Тестовые аккаунты по умолчанию**
- **Админ**: `admin` / `admin123` (Доступ к админ-панели)
- **Обычный пользователь**: `testuser` / `test123`

### **Для администраторов**
1. **Доступ к панели**: Перейти на `/admin` (требуется роль админа)
2. **Управление контентом**:
   - Запускать веб-парсеры для новых данных
   - Модерировать пользовательские оценки и отзывы
   - Управлять аккаунтами пользователей и разрешениями
3. **Мониторинг системы**: Просматривать аналитику и статистику системы

### **Примеры запросов в чат**
- "Найти романтический итальянский ресторан в центре"
- "Лучшие кофейни с уличной посадкой и Wi-Fi"
- "Семейные развлечения на выходные"
- "Модные бары с живой музыкой поблизости"

## **Документация API**

После запуска посетите `http://localhost:8000/docs` для полной интерактивной документации API

- **Эндпоинты аутентификации** (`/api/auth/`)
- **Эндпоинты чата** (`/api/chat/`)
- **Эндпоинты заведений** (`/api/venues/`)
- **Админ-эндпоинты** (`/api/admin/`)

## **Устранение неполадок**

| Проблема | Решение |
|-------|----------|
| **Ошибки подключения к LocalAI** | Проверить доступность `LOCALAI_BASE_URL`, убедиться что модель загружена |
| **Ошибки gRPC ChromaDB** | Установить `CHROMA_SERVER_HOST=0.0.0.0` в окружении |
| **Redis connection refused** | Убедиться что имя сервиса `redis` (не `localhost`) |
| **SQLite unique constraint** | Удалить существующего пользователя или использовать другое имя |
| **Конфликты портов** | Обновить порты в `docker-compose.yml` |
| **Недостаточно памяти** | Уменьшить threads LocalAI или использовать меньшие модели |

## **Мониторинг и аналитика**

Система включает встроенную аналитику с ClickHouse:

- **Отслеживание взаимодействий пользователей**
- **Аналитика оценок заведений**
- **Метрики производительности LLM**
- **Статистика использования системы**

Доступ через:
```bash
docker-compose exec clickhouse clickhouse-client

```
