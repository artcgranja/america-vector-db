# src/app/vectorization/vector_store.py
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from app.core.config import settings

def get_vector_store(collection_name: str):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    return PGVector(
        embeddings=embeddings,
        connection=settings.database_url,
        collection_name=collection_name,
        distance_strategy="COSINE",
        use_jsonb=True
    )