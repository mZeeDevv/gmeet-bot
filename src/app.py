from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "fastn-bot",
        "version": "1.0.0"
    })

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        # Get search results from vector store
        search_results = search_docs(query)
        
        if not search_results:
            return jsonify({
                'answer': 'No relevant information found in the documentation.',
                'sources': []
            })

        # Generate answer using Gemini
        answer = generate_answer(query, search_results)

        # Return both the answer and the sources
        return jsonify({
            'answer': answer,
            'sources': search_results  # This includes URLs and other metadata
        })

    except Exception as e:
        print(f"Error during search: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)