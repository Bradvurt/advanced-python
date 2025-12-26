from redisvl.utils.vectorize import CustomTextVectorizer
from redisvl.extensions.llmcache import SemanticCache
from langchain.embeddings import LocalAIEmbeddings
import redis.asyncio as redis
from typing import Optional
import json
import asyncio
from typing import List
from app.config import settings

class CustomSemanticCache(SemanticCache):
    def __init__(self):
        super().__init__(
            name="VenueLLMCache",
            redis_url=settings.REDIS_URL,
            distance_threshold=0.1,
            vectorizer=create_vectorizer(),
            connection_kwargs={
                'decode_responses': True,
                'socket_timeout': 5,
                'retry_on_timeout': True
            },
            dimension=768
        )

def create_vectorizer():
    # Initialize LocalAIEmbeddings
    embedding=LocalAIEmbeddings(
            openai_api_base=settings.LOCALAI_BASE_URL,
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            embedding_ctx_length = settings.EMBEDDING_CTX_LENGTH
            )

    # Define the synchronous embedding function
    def sync_embed(text: str) -> List[float]:
        return embedding.embed_query(text)

    # Define the synchronous batch embedding function
    def sync_embed_many(texts: List[str]) -> List[List[float]]:
        return embedding.embed_documents(texts)

    # Define a wrapper for async single-text embedding
    async def async_embed(text: str) -> List[float]:
        # Run the synchronous method in a separate thread
        return await asyncio.to_thread(sync_embed, text)

    # Define a wrapper for async batch embedding
    async def async_embed_many(texts: List[str]) -> List[List[float]]:
        # Run the synchronous method in a separate thread
        return await asyncio.to_thread(sync_embed_many, texts)

    # Configure and return CustomTextVectorizer
    return CustomTextVectorizer(
        embed=sync_embed,
        aembed=async_embed,
        embed_many=sync_embed_many,
        aembed_many=async_embed_many
    )