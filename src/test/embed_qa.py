import json
import os
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Setup paths
SCRIPT_DIR = Path(__file__).parent.absolute()

# Load environment variables
load_dotenv()

# Get Qdrant cloud credentials
QDRANT_HOST = os.getenv("QDRANT_HOST")  # Your cluster URL
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # Your API key

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

def verify_collection():
    """Verify that the collection exists and print its info."""
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        print(f"Collection info:")
        print(f"- Points count: {collection_info.points_count}")
        print(f"- Vectors size: {collection_info.config.params.vectors.size}")
        return True
    except Exception as e:
        print(f"Collection not found: {str(e)}")
        return False

# Constants
COLLECTION_NAME = "test_qa"
VECTOR_SIZE = 384  # Embedding dimension for all-MiniLM-L6-v2

def create_collection():
    """Create Qdrant collection for storing Q&A embeddings."""
    try:
        qdrant_client.get_collection(COLLECTION_NAME)
        print(f"Collection {COLLECTION_NAME} already exists")
    except:
        # Create new collection if it doesn't exist
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE
            )
        )
        print(f"Created new collection: {COLLECTION_NAME}")

def embed_qa_pairs():
    """Load and embed Q&A pairs into Qdrant."""
    qa_file = SCRIPT_DIR / 'qa_data.json'
    print(f"Loading Q&A data from: {qa_file}")
    
    # Load the Q&A data
    with open(qa_file, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    # Create collection
    create_collection()
    
    # Process each Q&A pair
    points = []
    for i, qa_pair in enumerate(qa_data['qa_pairs']):
        # Create combined text for embedding (question and answer)
        question = qa_pair['question']
        answer = qa_pair['answer']
        
        print(f"Processing Q&A pair {i+1}:")
        print(f"Q: {question}")
        print(f"A: {answer}")
        
        # Create embeddings for both question and answer
        question_embedding = model.encode(question)
        answer_embedding = model.encode(answer)
        
        # Create points for both question and answer
        question_point = models.PointStruct(
            id=i * 2,  # Even IDs for questions
            vector=question_embedding.tolist(),
            payload={
                'type': 'question',
                'text': question,
                'answer': answer
            }
        )
        
        answer_point = models.PointStruct(
            id=i * 2 + 1,  # Odd IDs for answers
            vector=answer_embedding.tolist(),
            payload={
                'type': 'answer',
                'text': answer,
                'question': question
            }
        )
        
        points.extend([question_point, answer_point])
    
    # Upload points to Qdrant
    print("Uploading points to Qdrant...")
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    
    print(f"Successfully embedded {len(qa_data['qa_pairs'])} Q&A pairs ({len(points)} points total)")
    
    # Verify the upload
    time.sleep(1)  # Give Qdrant a moment to process
    verify_collection()

if __name__ == "__main__":
    print("Starting Q&A embedding process...")
    embed_qa_pairs()
    print("\nFinished! To verify, run search_qa.py to test searching through the embeddings.")
    # First verify if collection exists
    print("\nVerifying existing collection:")
    if verify_collection():
        print("Collection already exists!")
        choice = input("Do you want to recreate the collection? (y/n): ")
        if choice.lower() != 'y':
            print("Exiting without changes.")
            exit()
    
    print("\nEmbedding Q&A pairs:")
    embed_qa_pairs()
    
    print("\nVerifying after embedding:")
    verify_collection()