# AI response generation using Google Gemini

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class AIResponder:
    """Handles AI response generation with Gemini"""
    
    def __init__(self, vector_searcher=None):
        self.gemini_model = None
        self.system_context = """You are a helpful AI assistant in a Google Meet call. 
You can answer any general questions about various topics."""
        self.vector_searcher = vector_searcher
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini AI model"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("GEMINI_API_KEY not found in .env file")
                self.gemini_model = None
                return
            
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-pro')
            print("Gemini AI initialized successfully")
        except Exception as e:
            print(f"Error initializing Gemini: {str(e)}")
            self.gemini_model = None
    
    def set_vector_searcher(self, vector_searcher):
        """Set the vector searcher for documentation queries"""
        self.vector_searcher = vector_searcher
    
    def generate_response(self, user_question):
        """Generate AI response using Gemini with vector search context"""
        try:
            if not self.gemini_model:
                return "I'm having trouble with my AI connection. Could you please repeat that?", []
            
            citations = []
            context = ""
            
            if self.vector_searcher and self.vector_searcher.is_available():
                print("Searching documentation...")
                results, citations = self.vector_searcher.search_docs(user_question, limit=3)
                
                if results:
                    context = self.vector_searcher.format_context_for_ai(results)
                    print(f"Found {len(results)} relevant documents")
            
            if context:
                prompt = f"""You are an AI assistant for Fastn.ai in a Google Meet call.
Use the following documentation to answer the user's question accurately.
Keep your response concise (2-3 sentences) and speak naturally as if in a conversation.

Documentation Context:
{context}

User question: {user_question}

Provide a clear, concise answer based on the documentation:"""
            else:
                prompt = f"""{self.system_context}

User question: {user_question}

Provide a helpful, concise response (2-3 sentences):"""
            
            response = self.gemini_model.generate_content(prompt)
            answer = response.text.strip()
            
            return answer, citations
            
        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return "I'm sorry, I couldn't process that. Could you rephrase your question?", []
