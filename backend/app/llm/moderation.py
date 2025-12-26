from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI

from app.config import settings

class LlamaGuardModerator:
    def __init__(self):

        # Инициализация модели Llama Guard для модерации контента
        self.llm = ChatOpenAI(
            openai_api_base=settings.LOCALAI_BASE_URL,
            openai_api_key=settings.OPENAI_API_KEY,
            model="llama-guard-3-8b",  # Специализированная модель для модерации
            temperature=0  # Детерминированные ответы для консистентности
        )
        
        # Шаблон промпта для оценки безопасности запросов
        self.moderation_prompt = PromptTemplate(
            input_variables=["query"],
            template="""
            Проанализируй следующий запрос пользователя на безопасность и уместность.
            Верни только "safe" (безопасно) или "unsafe" (небезопасно) в качестве ответа.
            
            Запрос: {query}
            
            Учитывай следующие категории:
            1. Насилие, разжигание ненависти, преследование
            2. Незаконная деятельность
            3. Запросы личной информации
            4. Неуместный контент
            
            Ответ:
            """
        )
        
        # Создание LLM цепочки для модерации
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.moderation_prompt
        )
    
    async def execute_query(self, query: str) -> bool:
        """
        Модерация пользовательского запроса с использованием Llama Guard.
        
        Процесс:
        1. Передача запроса в модель Llama Guard через LLM цепочку
        2. Анализ запроса на соответствие критериям безопасности
        3. Возврат булева значения на основе ответа модели
        
        Args:
            query: Текстовый запрос пользователя для модерации
        
        Returns:
            bool: True - запрос безопасен, False - запрос небезопасен или произошла ошибка
        
        Note:
            В случае ошибки модерации возвращается False (небезопасно) по умолчанию
        """
        try:
            # Выполнение модерации через LLM цепочку
            result = await self.chain.arun(query=query)
            print(f"Ответ Llama Guard: {result}")
            
            # Парсинг ответа: безопасно если результат содержит "safe"
            return result.strip().lower() == "safe"
        except Exception as e:
            print(f"Ошибка модерации: {e}")
            # По умолчанию считаем небезопасным при ошибке для безопасности
            return False