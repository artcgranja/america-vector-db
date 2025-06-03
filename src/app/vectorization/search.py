from typing import List, Dict
from datetime import datetime, timedelta

class SearchFilter:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        
    def apply_filters(self, query: str, filters: Dict = None) -> Dict:
        base_filters = {
            "document_type": "MPV",  # Prioritize MPV documents
            "hierarchy_level": 0,    # Main documents only
        }
        
        if filters:
            base_filters.update(filters)
            
        # Add temporal filters if needed
        if "time_range" in filters:
            base_filters["timestamp"] = {
                "$gte": datetime.now() - timedelta(days=filters["time_range"])
            }
            
        return base_filters

class HybridSearch:
    def __init__(self, vector_store, search_filter: SearchFilter):
        self.vector_store = vector_store
        self.search_filter = search_filter
        
    def search(self, query: str, k: int = 4, filters: Dict = None):
        # Apply pre-search filters
        search_filters = self.search_filter.apply_filters(query, filters)
        
        # Perform hybrid search (vector + keyword)
        vector_results = self.vector_store.similarity_search(
            query,
            k=k,
            filter=search_filters
        )
        
        # Apply post-search reranking
        reranked_results = self._rerank_results(vector_results, query)
        
        return reranked_results[:k]
