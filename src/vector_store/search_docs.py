import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import google.generativeai as genai

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel('gemini-2.5-pro')
model = SentenceTransformer('all-MiniLM-L6-v2')

print(f"Connecting to Qdrant Cloud at: {QDRANT_HOST}")
qdrant_client = QdrantClient(
    url=QDRANT_HOST,
    api_key=QDRANT_API_KEY
)

COLLECTION_NAME = "fastn_documentation"

def search_docs(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    query_embedding = model.encode(query)
    
    search_results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=limit
    )
    
    results = []
    for result in search_results:
        results.append({
            'score': result.score,
            'text': result.payload['text'],
            'url': result.payload['url'],
            'has_code': result.payload.get('has_code', False)
        })
    
    return results

def generate_answer(query: str, results: List[Dict[str, Any]]) -> str:
    context = "\n\n".join([f"Content from {r['url']}:\n{r['text']}" for r in results])
    
    prompt = f"""You are an expert on the FASTN documentation. Your task is to provide a detailed and comprehensive answer to the user's question, based *only* on the provided documentation content.

User's Question: "{query}"

Here is the relevant documentation content retrieved from our vector database:
---
{context}
---

Please synthesize the information from the provided content to construct a thorough answer. Structure your response in a clear and easy-to-read format. Use headings, lists, and code blocks if appropriate.

After providing the answer, list the URLs of the source documents you used to generate the answer.

If the provided documentation does not contain enough information to answer the question, state that clearly and do not attempt to answer from outside knowledge.

Your final output should be a single, complete response.
"""

    try:
        response = llm.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

def format_result(result: Dict[str, Any]) -> str:
    """Format a single search result for display."""
    return f"""
Source URL: {result['url']}
{'[Contains Code Example]' if result['has_code'] else ''}
---
{result['text']}
---
"""

def interactive_search():
    """Interactive command-line interface for searching documentation."""
    print("\nFASTN Documentation Search with AI")
    print("Type 'quit' or 'exit' to end the session")
    print("Type 'sources' after getting an answer to see the source documentation")
    print("-" * 50)
    
    while True:
        # Get user input
        query = input("\nEnter your question: ").strip()
        
        # Check for exit command
        if query.lower() in ['quit', 'exit']:
            break
        
        if not query:
            continue
        
        # Search for answers
        print("\nSearching and generating answer...")
        try:
            results = search_docs(query)
            
            if not results:
                print("No relevant information found in the documentation.")
                continue
            
            # Generate and display AI answer
            answer = generate_answer(query, results)
            print("\nAnswer:")
            print("-" * 50)
            print(answer)
            print("-" * 50)
            
            # Ask if user wants to see sources
            show_sources = input("\nWould you like to see the source documentation? (y/n): ").lower().strip()
            if show_sources == 'y':
                print("\nSource Documentation:")
                for i, result in enumerate(results, 1):
                    print(f"\nSource {i}:{format_result(result)}")
                
        except Exception as e:
            print(f"Error during search: {str(e)}")
    
    print("\nThank you for using FASTN Documentation Search!")

if __name__ == "__main__":
    # Verify collection exists
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        print(f"Connected to collection '{COLLECTION_NAME}' with {collection_info.points_count} points")
        interactive_search()
    except Exception as e:
        print(f"Error: {str(e)}")