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
            
            # PERFORMANCE: Use fastest model for quickest responses
            # gemini-2.5-flash-lite: FASTEST (1-2 sec) - Best for real-time chat
            # gemini-2.5-flash: Fast (2-3 sec) - Good balance
            # gemini-2.5-pro: Slower (4-5 sec) - Highest quality
            model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
            
            self.gemini_model = genai.GenerativeModel(model_name)
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
                # Reduced from 3 to 2 results for faster processing
                results, citations = self.vector_searcher.search_docs(user_question, limit=2)
                
                if results:
                    context = self.vector_searcher.format_context_for_ai(results)
                    
                    # PERFORMANCE: Truncate context to reduce AI processing time
                    if len(context) > 1500:
                        context = context[:1500] + "...(truncated for speed)"
            
            if context:
                # Shorter, more focused prompt for faster response
                prompt = f"""You are an AI assistant for Fastn.ai in a Google Meet call.
Answer concisely (2-3 sentences) using this documentation:

{context}

Question: {user_question}
Answer:"""
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
