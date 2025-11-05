import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Get Qdrant cloud credentials
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_HOST or not QDRANT_API_KEY:
    raise ValueError("Please set QDRANT_HOST and QDRANT_API_KEY in your .env file")

# Initialize Qdrant client with cloud configuration
print(f"Connecting to Qdrant Cloud at: {QDRANT_HOST}")
qdrant_client = QdrantClient(
    url=QDRANT_HOST,
    api_key=QDRANT_API_KEY,
)

# Check collection info
try:
    collection_info = qdrant_client.get_collection("test_qa")
    print("\nCollection Information:")
    print(f"Collection name: test_qa")
    print(f"Vector size: {collection_info.config.params.vectors.size}")
    print(f"Number of points: {collection_info.points_count}")
    print(f"Status: {collection_info.status}")
except Exception as e:
    print(f"\nError: {str(e)}")
    print("It seems the collection doesn't exist. You may need to run embed_qa.py first to create and populate it.")