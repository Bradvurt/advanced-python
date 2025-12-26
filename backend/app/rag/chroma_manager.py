# backend/app/rag/chroma_manager.py
from langchain.vectorstores import Chroma
from langchain_core.documents import Document
from langchain.embeddings import LocalAIEmbeddings
from typing import List, Dict, Any, Optional
import uuid
from app.config import settings
import chromadb
from chromadb.config import Settings

class ChromaManager:
    def __init__(self):
        self.embedding_function = LocalAIEmbeddings(
            openai_api_base=settings.LOCALAI_BASE_URL,
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            embedding_ctx_length=settings.EMBEDDING_CTX_LENGTH
        )
        self.vectorstore = Chroma(
            collection_name="venue_data",
            embedding_function=self.embedding_function,
            persist_directory=settings.CHROMA_PERSIST_DIR,  # Включение персистентности данных
            # collection_metadata={"hnsw:space": "cosine"}  # Метрика схожести (закомментировано)
        )

    def add_venues(self, venues: List[Dict[str, Any]]) -> int:
        """
        Добавление списка заведений в векторное хранилище.
        
        Преобразует данные о заведениях в документы LangChain, генерирует эмбеддинги
        и сохраняет в ChromaDB с персистентностью на диск.
        
        Args:
            venues: Список словарей с данными о заведениях
        
        Returns:
            int: Количество успешно добавленных заведений
        """
        print("Добавление заведений...")
        documents = []
        ids = []
        
        for venue in venues:
            # Создание текстового представления заведения
            doc_text = f"""
            Название: {venue.get('name', '')}
            Категория: {venue.get('category', '')}
            Адрес: {venue.get('address', '')}
            Оценка: {venue.get('rating', 0)}
            Часы работы: {venue.get('opening_hours', '')}
            Ссылка на Яндекс.Карты: {venue.get('ypage', '')}
            Товары и услуги: {venue.get('goods', '')}
            """
            # Отзывы: {venue.get('reviews', '')}
            
            # Создание метаданных для фильтрации
            metadata = {
                "name": venue.get("name", ""),
                "category": venue.get("category", ""),
                "rating": str(venue.get("rating", 0)),
                "source": venue.get("source", "parser")
            }
            
            # Создание объекта документа LangChain
            doc = Document(
                page_content=doc_text,
                metadata=metadata
            )
            documents.append(doc)
            
            # Генерация уникального ID (предпочтительно Yandex ID)
            venue_id = venue.get("yandex_id") or str(uuid.uuid4())
            print("YANDEX ID", venue_id)
            ids.append(venue_id)
        
        # Добавление документов в векторное хранилище через LangChain
        added_ids = self.vectorstore.add_documents(
            documents=documents,
            ids=ids
        )
        
        try:
            # Сохранение данных на диск для персистентности
            if hasattr(self.vectorstore, '_persist_directory') and self.vectorstore._persist_directory:
                self.vectorstore.persist()
                print(f"Сохранено {len(added_ids)} заведений на диск.")
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return False
        
        # Проверка содержимого коллекции (для отладки)
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        collection = client.get_collection("venue_data")
        collection_data = collection.get()
        print(collection_data)

        return len(added_ids)

    def search_similar(self, query: str, n_results: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Поиск семантически похожих заведений по текстовому запросу.
        
        Использует векторные эмбеддинги для поиска заведений, наиболее соответствующих
        смыслу запроса, с возможностью фильтрации по метаданным.
        
        Args:
            query: Текстовый запрос для поиска
            n_results: Количество возвращаемых результатов (по умолчанию 5)
            filters: Опциональные фильтры по метаданным (например, {"category": "Ресторан"})
        
        Returns:
            List[Dict[str, Any]]: Список найденных заведений с метаданными и оценкой схожести
        """
        try:
            # Выполнение семантического поиска с использованием векторного хранилища
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=n_results,
                filter=filters
            )
            
            venues = []
            for doc, score in results:
                # Преобразование расстояния в оценку схожести
                similarity_score = 1.0 / (1.0 + score) if score != 0 else 1.0
                
                venue = {
                    "id": doc.metadata.get("external_id", str(uuid.uuid4())),
                    "document": doc.page_content,
                    "metadata": doc.metadata,
                    "distance": score,
                    "score": similarity_score
                }
                venues.append(venue)
            
            return venues
            
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            return []
    
    def get_retriever(self, search_kwargs: Optional[Dict] = None):
        """
        Получение объекта retriever для использования в LangChain цепочках.
        
        Args:
            search_kwargs: Дополнительные параметры поиска
        
        Returns:
            Retriever: Объект retriever для интеграции с LangChain компонентами
        """
        return self.vectorstore.as_retriever(
            search_kwargs=search_kwargs or {"k": 5}
        )
    
    def delete_venues(self, ids: List[str]) -> bool:
        """
        Удаление заведений из векторного хранилища по их идентификаторам.
        
        Args:
            ids: Список идентификаторов заведений для удаления
        
        Returns:
            bool: True если удаление успешно, False в случае ошибки
        """
        try:
            self.vectorstore.delete(ids=ids)
            return True
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return False