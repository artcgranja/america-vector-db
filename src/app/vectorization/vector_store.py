# src/app/vectorization/vector_store.py
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from src.app.core.config import settings

class WeightedVectorStore:
    def __init__(self, collection_name: str):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            connection=settings.database_url,
            collection_name=collection_name,
            distance_strategy="cosine",
            use_jsonb=True
        )
        
    def similarity_search(self, query: str, k: int = 4, document_type: str = None):
        # Base search results
        results = self.vector_store.similarity_search(query, k=k*2)  # Get more results for reranking
        
        # Apply weights based on document type
        weights = {
            "MPV": 1.0,  # Base weight
            "EMENDA": 0.6,  # Lower weight for amendments
        }
        
        # Rerank results with weights
        weighted_results = []
        for doc in results:
            doc_type = doc.metadata.get("document_type", "MPV")
            weight = weights.get(doc_type, 1.0)
            doc.metadata["relevance_score"] = doc.metadata.get("score", 0) * weight
            weighted_results.append(doc)
            
        # Sort by weighted score and return top k
        weighted_results.sort(key=lambda x: x.metadata["relevance_score"], reverse=True)
        return weighted_results[:k]