from flask import Flask, render_template, request, jsonify
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vector_store.search_docs import search_docs, generate_answer

app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    return render_template('read_docs.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    print(f"Received query: {query}")

    try:
        # Perform the search and generate an answer
        search_results = search_docs(query)
        print(f"Search results: {search_results}")
        
        answer = generate_answer(query, search_results)
        print(f"Generated answer: {answer}")

        return jsonify({'answer': answer})
    except Exception as e:
        print(f"Error during search: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
    # Run without debug mode to avoid multiple Qdrant instances
    app.run(debug=False, port=5000)