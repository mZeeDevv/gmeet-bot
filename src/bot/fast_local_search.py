# Fast local documentation search without vector embeddings

import json
import os
from typing import List, Dict, Tuple
import re


class FastLocalSearcher:
    """
    Fast keyword-based search using local JSON file
    No embeddings, no vector database - just simple text matching
    """
    
    def __init__(self, docs_file="docs_content.json"):
        self.docs_data = {}
        self.docs_file = docs_file
        self._load_docs()
    
    def _load_docs(self):
        """Load documentation from JSON file"""
        try:
            docs_path = os.path.join(os.path.dirname(__file__), '..', self.docs_file)
            with open(docs_path, 'r', encoding='utf-8') as f:
                self.docs_data = json.load(f)
        except Exception as e:
            print(f"Error loading docs: {str(e)}")
            self.docs_data = {}
    
    def is_available(self) -> bool:
        """Check if the searcher is ready to use"""
        return bool(self.docs_data)
    
    def _calculate_relevance_score(self, query: str, doc_text: str, doc_url: str) -> float:
        """
        Calculate relevance score based on keyword matches
        Higher score = more relevant
        """
        query_lower = query.lower()
        text_lower = doc_text.lower()
        url_lower = doc_url.lower()
        
        score = 0.0
        
        # Extract important keywords from query (remove common words)
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'to', 'for', 'of', 'how', 'what', 'when', 'where', 'who', 'why', 'can', 'i', 'you', 'with'}
        keywords = [word for word in re.findall(r'\w+', query_lower) if word not in stop_words and len(word) > 2]
        
        if not keywords:
            return 0.0
        
        # BOOST: Exact phrase match (very important!)
        if query_lower in text_lower:
            score += 50.0  # Increased from 10.0
        
        # BOOST: Title/heading match (first 200 chars are usually titles)
        text_start = text_lower[:200]
        for keyword in keywords:
            if keyword in text_start:
                score += 10.0  # Big boost for keywords in title/start
        
        # BOOST: URL path matching (very valuable)
        for keyword in keywords:
            if keyword in url_lower:
                score += 8.0  # Increased from 5.0
        
        # Score based on keyword frequency in text
        for keyword in keywords:
            if keyword in text_lower:
                count = text_lower.count(keyword)
                # Diminishing returns for repetition
                score += min(count, 5) * 1.5
        
        # BOOST: Multi-word phrases from query
        if len(keywords) >= 2:
            # Check if keywords appear close together (within 50 chars)
            for i, kw1 in enumerate(keywords[:-1]):
                kw2 = keywords[i + 1]
                # Find if both keywords appear near each other
                idx1 = text_lower.find(kw1)
                if idx1 != -1:
                    nearby_text = text_lower[max(0, idx1-25):idx1+75]
                    if kw2 in nearby_text:
                        score += 15.0  # Keywords appear together
        
        # Normalize by document length to avoid bias toward long documents
        doc_length = len(doc_text)
        if doc_length > 0:
            # Less aggressive normalization to preserve good matches
            score = score / (doc_length / 2000)  # Changed from 1000 to 2000
        
        return score
    
    def _calculate_relevance_score_with_headings(self, query: str, doc_text: str, doc_url: str, doc_headings: list) -> float:
        """
        Enhanced scoring that considers headings for better accuracy
        """
        # Start with base score
        score = self._calculate_relevance_score(query, doc_text, doc_url)
        
        if not doc_headings:
            return score
        
        query_lower = query.lower()
        keywords = [word for word in re.findall(r'\w+', query_lower) if len(word) > 2]
        
        # MAJOR BOOST: Exact query match in any heading
        for heading in doc_headings:
            if isinstance(heading, dict):
                heading_text = heading.get('text', '').lower()
            else:
                heading_text = str(heading).lower()
            
            # Exact phrase in heading
            if query_lower in heading_text:
                score += 100.0  # Massive boost!
            
            # All keywords present in one heading
            elif all(kw in heading_text for kw in keywords):
                score += 50.0  # Strong boost
            
            # Individual keyword matches in headings
            else:
                for keyword in keywords:
                    if keyword in heading_text:
                        score += 10.0  # Good boost per keyword
        
        return score
    
    def search_docs(self, query: str, limit: int = 3) -> Tuple[List[Dict], List[str]]:
        """
        Search documentation using keyword matching
        Returns: (results, citations)
        """
        if not self.docs_data:
            return [], []
        
        try:
            # Score all documents
            scored_docs = []
            
            for url, content in self.docs_data.items():
                if not content or 'text' not in content:
                    continue
                
                doc_text = content['text']
                doc_headings = content.get('headings', [])
                
                # Skip very short documents (likely empty or nav-only)
                if len(doc_text) < 100:
                    continue
                
                # Calculate score with heading support
                score = self._calculate_relevance_score_with_headings(query, doc_text, url, doc_headings)
                
                # Only include docs with meaningful scores
                if score > 0.5:  # Threshold to filter noise
                    scored_docs.append({
                        'url': url,
                        'text': doc_text,
                        'score': score,
                        'has_code': bool(content.get('code_blocks', []))
                    })
            
            # Sort by score and get top results
            scored_docs.sort(key=lambda x: x['score'], reverse=True)
            top_results = scored_docs[:limit]
            
            # Extract citations
            citations = [doc['url'] for doc in top_results]
            
            # Truncate text for context (keep it short for faster AI processing)
            for doc in top_results:
                if len(doc['text']) > 2000:
                    doc['text'] = doc['text'][:2000] + "..."
            
            return top_results, citations
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return [], []
    
    def format_context_for_ai(self, results: List[Dict]) -> str:
        """Format search results for AI prompt"""
        if not results:
            return ""
        
        context_parts = []
        for i, doc in enumerate(results, 1):
            context_parts.append(f"Document {i} (from {doc['url']}):\n{doc['text']}")
        
        return "\n\n".join(context_parts)


# Singleton instance
_searcher = None

def get_searcher() -> FastLocalSearcher:
    """Get or create singleton searcher instance"""
    global _searcher
    if _searcher is None:
        _searcher = FastLocalSearcher()
    return _searcher
