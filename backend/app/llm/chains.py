import os
from typing import List, Dict, Any, Optional
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_community.embeddings import LocalAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.callbacks import CallbackManager
from langchain.chains import LLMChain
from langchain.vectorstores import Chroma

from app.config import settings
from app.rag.chroma_manager import ChromaManager

class StreamingCallbackHandler(BaseCallbackHandler):
    
    def on_llm_new_token(self, token: str, **kwargs):
        """Обработка нового токена, сгенерированного LLM."""
        print(f"Новый токен: {token}", end="", flush=True)

class RecommendationChain:
    
    def __init__(self):

        # Инициализация функции эмбеддингов
        self.embedding_function = LocalAIEmbeddings(
            openai_api_base=settings.LOCALAI_BASE_URL,
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            embedding_ctx_length=settings.EMBEDDING_CTX_LENGTH
        )
        
        # Инициализация языковой модели Gemma
        self.llm = ChatOpenAI(
            openai_api_base=settings.LOCALAI_BASE_URL,
            openai_api_key=settings.OPENAI_API_KEY,
            model='gemma-3-12b-it',
            temperature=0  # Температура 0 для детерминированных ответов
        )

        # Шаблон промпта для персонализированных рекомендаций
        self.prompt_template = PromptTemplate(
            input_variables=["question", "user_preferences"],
            template="""
            Ты ассистент для персонализированных рекомендаций мест отдыха и развлечений на основе предпочтений пользователей.
            
            Предпочтения пользователя: {user_preferences}
            
            Запрос: {question}

            Основываясь на этой информации, составь персонализированную рекомендацию.
            Указывай точные места из полученного контекста.
            Если информации недостаточно, спрашивай уточняющие вопросы.
            """
        )

        # Инициализация векторного хранилища Chroma с персистентностью
        self.vectorstore = Chroma(
            collection_name="venue_data",
            embedding_function=self.embedding_function,
            persist_directory=settings.CHROMA_PERSIST_DIR,  # Включение персистентности данных
            # collection_metadata={"hnsw:space": "cosine"}  # Метрика схожести
        )
        
        # Настройка retriever'а для извлечения релевантных документов
        target_source_chunks = 4  # Количество извлекаемых фрагментов
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": target_source_chunks})

        # Создание RetrievalQA цепочки
        self.chain = RetrievalQA.from_chain_type(
            llm=self.llm, 
            chain_type="stuff",  # Метод объединения контекста
            retriever=self.retriever, 
            return_source_documents=True  # Возврат исходных документов для отладки
        )
    
    async def execute_query(self, query: str, user_preferences: Dict[str, Any]) -> str:
        """
        Выполнение запроса пользователя с использованием RAG подхода.
        
        Процесс:
        1. Форматирование запроса с учетом предпочтений пользователя
        2. Поиск релевантных документов в векторной базе
        3. Генерация персонализированного ответа с использованием LLM
        4. Возврат ответа с возможной отладкой исходных документов
        
        Args:
            query: Текстовый запрос пользователя
            user_preferences: Словарь с предпочтениями пользователя (бюджет, кухня и т.д.)
        
        Returns:
            str: Сгенерированный ответ с рекомендациями
        
        Note:
            В случае ошибки возвращает строку "Error" для обработки на уровне API
        """
        try:
            print(f"Запрос: {query}, Предпочтения: {user_preferences}")
            
            # Выполнение запроса через RetrievalQA цепочку
            res = self.chain(query)
            answer, docs = res['result'], res['source_documents']
            
            print(f"Результат: {res}")
            return answer
        except Exception as e:
            print(f"Ошибка выполнения: {e}")
            return "Error"