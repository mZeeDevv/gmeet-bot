import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Get Qdrant cloud credentials
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_HOST or not QDRANT_API_KEY:
    raise ValueError("Please set QDRANT_HOST and QDRANT_API_KEY in your .env file")

# Initialize the embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Qdrant client with cloud configuration
print(f"Connecting to Qdrant Cloud at: {QDRANT_HOST}")
qdrant_client = QdrantClient(
    url=QDRANT_HOST,
    api_key=QDRANT_API_KEY,
)

COLLECTION_NAME = "test_qa"

def search_and_get_answer(query: str, limit: int = 3):
    """Search for relevant answers based on the query."""
    # Create embedding for the query
    query_embedding = model.encode(query)
    
    # Search in Qdrant
    search_results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=limit
    )
    
    if not search_results:
        return "I couldn't find a relevant answer to your question."
    
    # Get the best match
    best_match = search_results[0]
    
    # Format response
    response = {
        'confidence': best_match.score,
        'question': best_match.payload.get('question', query) if best_match.payload['type'] == 'answer' else best_match.payload['text'],
        'answer': best_match.payload.get('answer', best_match.payload['text']) if best_match.payload['type'] == 'question' else best_match.payload['text']
    }
    
    return response

def main():
    print("\nWelcome to the FASTN Q&A System!")
    print("Type 'quit' or 'exit' to end the session")
    print("-" * 50)
    
    while True:
        # Get user input
        query = input("\nYour question: ").strip()
        
        # Check for exit command
        if query.lower() in ['quit', 'exit']:
            print("Thank you for using FASTN Q&A System. Goodbye!")
            break
        
        if not query:
            print("Please enter a question.")
            continue
        
        # Get answer
        result = search_and_get_answer(query)
        
        if isinstance(result, str):
            print("\nResponse:", result)
        else:
            print("\nBest Match:")
            print(f"Confidence: {result['confidence']:.4f}")
            print(f"Question: {result['question']}")
            print(f"Answer: {result['answer']}")
        
        print("\n" + "-" * 50)

if __name__ == "__main__":
    try:
        # Verify collection exists
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        print(f"Connected to collection '{COLLECTION_NAME}' with {collection_info.points_count} points")
        main()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure you have run embed_qa.py first to create and populate the collection.")