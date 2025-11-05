import json
import os
from typing import List, Dict, Any
from tqdm import tqdm
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Initialize the embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast and efficient model

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

# Constants
COLLECTION_NAME = "fastn_documentation"  # Main collection for documentation
CHUNK_SIZE = 512  # Characters per chunk
VECTOR_SIZE = 384  # Embedding dimension for all-MiniLM-L6-v2
MAX_TOKENS = 256  # Maximum tokens for each chunk

def create_collection() -> None:
    """Create Qdrant collection for storing document embeddings."""
    try:
        qdrant_client.get_collection(COLLECTION_NAME)
    except:
        # Create new collection if it doesn't exist
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,  # Embedding dimension
                distance=models.Distance.COSINE
            )
        )

def process_docs_content(file_path: str) -> None:
    """Process the docs_content.json file and store embeddings in Qdrant."""
    # Load the JSON file
    print(f"Loading documentation from: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        docs_content = json.load(f)
    
    # Create collection if it doesn't exist
    create_collection()
    print("Collection ready for embeddings")
    
    # Process each document
    batch_size = 100
    points = []
    doc_id = 0
    total_urls = len(docs_content)
    
    for url, content in tqdm(docs_content.items(), desc="Processing documents", total=total_urls):
        # Extract content parts
        doc_text = content.get('text', '').strip()
        headings = content.get('headings', [])
        code_blocks = content.get('code_blocks', [])
        
        # Skip empty documents
        if not doc_text and not headings and not code_blocks:
            continue
            
        # Create a section header from the URL
        section = url.split('#')[-1].replace('-', ' ').title()
        
        # Process main text with headers for context
        if doc_text:
            # Add headers for context
            header_context = ' > '.join(headings) if headings else section
            context_text = f"Section: {header_context}\n\n{doc_text}"
            
            # Split into chunks
            chunks = chunk_text(context_text)
            
            # Process each chunk
            for chunk_idx, chunk in enumerate(chunks):
                # Create embedding
                embedding = model.encode(chunk)
                
                # Create Qdrant point
                point = models.PointStruct(
                    id=doc_id,
                    vector=embedding.tolist(),
                    payload={
                        "text": chunk,
                        "url": url,
                        "section": section,
                        "headings": headings,
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks),
                        "has_code": False,
                        "type": "documentation"
                    }
                )
                points.append(point)
                doc_id += 1
        
        # Process code blocks separately to maintain context
        if code_blocks:
            code_context = f"Section: {section} (Code Examples)"
            for code_idx, code in enumerate(code_blocks):
                if not code.strip():
                    continue
                
                # Create embedding for code with context
                code_with_context = f"{code_context}\n\n{code}"
                embedding = model.encode(code_with_context)
                
                # Create Qdrant point for code
                point = models.PointStruct(
                    id=doc_id,
                    vector=embedding.tolist(),
                    payload={
                        "text": code,
                        "url": url,
                        "section": section,
                        "headings": headings,
                        "code_index": code_idx,
                        "has_code": True,
                        "type": "code_example"
                    }
                )
                points.append(point)
                doc_id += 1
        
        # Upload in batches
        if len(points) >= batch_size:
            print(f"\nUploading batch of {len(points)} points...")
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            points = []
    
    # Upload remaining points
    if points:
        print(f"\nUploading final batch of {len(points)} points...")
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
    
    print(f"\nProcessing complete!")
    print(f"Total documents processed: {total_urls}")
    print(f"Total chunks stored: {doc_id}")
    
    # Verify the upload
    collection_info = qdrant_client.get_collection(COLLECTION_NAME)
    print(f"\nCollection Info:")
    print(f"- Points count: {collection_info.points_count}")
    print(f"- Vectors size: {collection_info.config.params.vectors.size}")
    print(f"Status: {collection_info.status}")

def chunk_text(text: str) -> List[str]:
    """Split text into chunks based on character count."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1  # +1 for space
        if current_length + word_length > CHUNK_SIZE:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks



if __name__ == "__main__":
    docs_path = os.path.join(os.path.dirname(__file__), '..', 'docs_content.json')
    process_docs_content(docs_path)
    print("Completed processing documents and storing embeddings.")