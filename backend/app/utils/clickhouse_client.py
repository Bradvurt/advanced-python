from clickhouse_driver import Client
from typing import Dict, Any, List
from datetime import datetime
import json

from app.config import settings

class ClickHouseMetrics:    
    def __init__(self):
        self.client = Client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database='default'
        )
        self._initialize_tables()
    
    def _initialize_tables(self):
        """
        Инициализация таблиц ClickHouse для хранения метрик.
        
        Создает три основные таблицы, если они не существуют:
        1. user_interactions - взаимодействия пользователей с системой
        2. venue_metrics - действия, связанные с заведениями
        3. llm_metrics - метрики работы языковых моделей
        
        Таблицы используют движок MergeTree, оптимизированный для аналитических запросов
        и временных рядов, с указанием ключей сортировки для эффективного поиска.
        """
        tables = [
            """
            CREATE TABLE IF NOT EXISTS user_interactions (
                timestamp DateTime,
                user_id Int32,
                session_id String,
                action String,
                details String,
                duration Float32
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, user_id)
            """,
            """
            CREATE TABLE IF NOT EXISTS venue_metrics (
                timestamp DateTime,
                venue_id Int32,
                action String,
                rating Nullable(Float32),
                review_length Nullable(Int32),
                user_id Int32
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, venue_id)
            """,
            """
            CREATE TABLE IF NOT EXISTS llm_metrics (
                timestamp DateTime,
                session_id String,
                query_length Int32,
                response_length Int32,
                processing_time Float32,
                cache_hit UInt8,
                moderation_result String
            ) ENGINE = MergeTree()
            ORDER BY timestamp
            """
        ]
        
        for table_sql in tables:
            try:
                self.client.execute(table_sql)
            except Exception as e:
                print(f"Ошибка создания таблицы: {e}")
    
    def log_interaction(self, user_id: int, session_id: str, action: str, details: Dict[str, Any], duration: float = 0):
        """
        Логирование взаимодействия пользователя с системой.
        
        Записывает в базу данных информацию о действиях пользователя,
        таких как отправка сообщений, просмотр заведений, навигация по интерфейсу.
        
        Args:
            user_id: Уникальный идентификатор пользователя
            session_id: Идентификатор сессии пользователя
            action: Тип действия (chat_message, venue_view, search_query и т.д.)
            details: Дополнительные детали действия в формате словаря
            duration: Длительность действия в секундах (по умолчанию 0)
        """
        query = """
        INSERT INTO user_interactions (timestamp, user_id, session_id, action, details, duration)
        VALUES (%(timestamp)s, %(user_id)s, %(session_id)s, %(action)s, %(details)s, %(duration)s)
        """
        
        self.client.execute(query, {
            'timestamp': datetime.now(),
            'user_id': user_id,
            'session_id': session_id,
            'action': action,
            'details': json.dumps(details),
            'duration': duration
        })
    
    def log_venue_action(self, venue_id: int, action: str, user_id: int, rating: float = None, review: str = None):
        """
        Логирование действий, связанных с заведениями.
        
        Записывает информацию о просмотрах заведений, выставленных оценках,
        оставленных отзывах и других действиях пользователей с веню.
        
        Args:
            venue_id: Уникальный идентификатор заведения
            action: Тип действия (view, rate, review, bookmark и т.д.)
            user_id: Идентификатор пользователя, выполнившего действие
            rating: Оценка заведения (опционально, для действий типа 'rate')
            review: Текст отзыва (опционально, для действий типа 'review')
        
        Note:
            Для действий типа 'rate' рекомендуется указывать rating.
            Для действий типа 'review' рекомендуется указывать review.
            Параметр review_length автоматически вычисляется из длины review.
        """
        query = """
        INSERT INTO venue_metrics (timestamp, venue_id, action, rating, review_length, user_id)
        VALUES (%(timestamp)s, %(venue_id)s, %(action)s, %(rating)s, %(review_length)s, %(user_id)s)
        """
        
        self.client.execute(query, {
            'timestamp': datetime.now(),
            'venue_id': venue_id,
            'action': action,
            'rating': rating,
            'review_length': len(review) if review else None,
            'user_id': user_id
        })