from flask import Flask, render_template, request, jsonify
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path to import search_docs
sys.path.append(str(Path(__file__).parent.parent))
from vector_store.search_docs import search_docs, generate_answer

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('search.html')

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