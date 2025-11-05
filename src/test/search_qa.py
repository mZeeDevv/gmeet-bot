from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os

# Initialize the embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Qdrant client with persistent storage
QDRANT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qdrant_db")
qdrant_client = QdrantClient(path=QDRANT_PATH)

# Constants
COLLECTION_NAME = "test_qa"

def search_qa(query: str, limit: int = 3):
    """Search for relevant Q&A pairs based on the query."""
    # Create embedding for the query
    query_embedding = model.encode(query)
    
    # Search in Qdrant
    search_results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=limit
    )
    
    # Format results
    results = []
    for hit in search_results:
        result = {
            'score': hit.score,
            'text': hit.payload['text'],
            'type': hit.payload['type']
        }
        
        # Include the corresponding question/answer
        if hit.payload['type'] == 'question':
            result['answer'] = hit.payload['answer']
        else:
            result['question'] = hit.payload['question']
            
        results.append(result)
    
    return results

if __name__ == "__main__":
    # Test the search
    test_queries = [
        "What is Paris?",
        "How do you bake a cake?",
        "Explain computer memory"
    ]
    
    print("Testing search functionality:")
    print("-" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = search_qa(query)
        for i, result in enumerate(results, 1):
            print(f"\nResult {i} (Score: {result['score']:.4f}):")
            print(f"Type: {result['type']}")
            print(f"Content: {result['text']}")
            if result['type'] == 'question':
                print(f"Answer: {result['answer']}")
            else:
                print(f"Question: {result['question']}")
        print("-" * 50)