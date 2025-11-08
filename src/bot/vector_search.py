# Vector search module for querying Fastn.ai documentation from Qdrant

import os
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

load_dotenv()

class VectorSearcher:
    def __init__(self):
        self.qdrant_host = os.getenv("QDRANT_HOST")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = "fastn_documentation"
        self.model = None
        self.client = None
        
        self._initialize()
    
    def _initialize(self):
        try:
            if not self.qdrant_host or not self.qdrant_api_key:
                print(" Qdrant credentials not found in .env - Vector search disabled")
                return
            
            print("Loading embedding model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            print(f"onnecting to Qdrant Cloud...")
            self.client = QdrantClient(
                url=self.qdrant_host,
                api_key=self.qdrant_api_key
            )
            
            try:
                collection_info = self.client.get_collection(self.collection_name)
                print(f"Connected to '{self.collection_name}' ({collection_info.points_count} documents)")
            except Exception as e:
                print(f"Collection '{self.collection_name}' not found: {str(e)}")
                self.client = None
                
        except Exception as e:
            print(f"Vector search initialization error: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        return self.client is not None and self.model is not None
    
    def search_docs(self, query: str, limit: int = 3) -> Tuple[List[Dict[str, Any]], List[str]]:
        if not self.is_available():
            return [], []
        
        try:
            query_embedding = self.model.encode(query)
            
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit
            )
            
            results = []
            citations = []
            
            for result in search_results:
                doc = {
                    'score': result.score,
                    'text': result.payload['text'],
                    'url': result.payload['url'],
                    'has_code': result.payload.get('has_code', False)
                }
                results.append(doc)
                
                if doc['url'] not in citations:
                    citations.append(doc['url'])
            
            print(f"Found {len(results)} relevant documents")
            return results, citations
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return [], []
    
    def format_context_for_ai(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return ""
        
        context_parts = []
        for i, doc in enumerate(results, 1):
            context_parts.append(f"Document {i} (from {doc['url']}):\n{doc['text']}")
        
        return "\n\n".join(context_parts)


_searcher = None

def get_searcher() -> VectorSearcher:
    global _searcher
    if _searcher is None:
        _searcher = VectorSearcher()
    return _searcher