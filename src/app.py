from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Load environment variables
    load_dotenv()

    # Add the parent directory to the Python path to import vector_store
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir))
    
    # Import search functionality
    from vector_store.search_docs import search_docs, generate_answer

    app = Flask(__name__, 
                template_folder=os.path.join(current_dir, 'templates'),
                static_folder=os.path.join(current_dir, 'static'))
    CORS(app)

    # Favicon route
    @app.route('/favicon.ico')
    def favicon():
        return '', 204  # No content response for favicon

    @app.route('/')
    def home():
        logger.info("Serving search template")
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
            logger.error(f"Error during search: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

    @app.errorhandler(404)
    def not_found(e):
        logger.error(f"Not found: {str(e)}")
        return jsonify({
            "error": "Not found",
            "message": str(e)
        }), 404

except Exception as e:
    logger.error(f"Error during app initialization: {str(e)}")
    raise

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