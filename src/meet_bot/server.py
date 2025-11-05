from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from threading import Thread
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment
PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
from pyngrok import ngrok

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Meet add-on communication

class MeetBotServer:
    def __init__(self, host="0.0.0.0", port=8080):
        self.host = host
        self.port = port
        self.app = app
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def home():
            """Home page with basic status"""
            return jsonify({
                "status": "online",
                "service": "fastn-bot",
                "version": "1.0.0",
                "endpoints": {
                    "webhook": "/webhook",
                    "health": "/api/health",
                    "test": "/api/test"
                }
            })

        @self.app.route('/api/test', methods=['GET'])
        def test_endpoint():
            """Test endpoint to verify the server is working"""
            return jsonify({
                "message": "Server is working correctly",
                "project_id": PROJECT_ID,
                "environment": os.getenv('ENV', 'development')
            })

        @self.app.route('/webhook', methods=['POST'])
        def handle_meet_event():
            """Handle incoming Meet add-on events"""
            try:
                data = request.json
                event_type = data.get('type')
                
                if event_type == 'JOIN':
                    # Handle when bot joins the meeting
                    return self._handle_join(data)
                elif event_type == 'MESSAGE':
                    # Handle incoming messages/questions
                    return self._handle_message(data)
                elif event_type == 'LEAVE':
                    # Handle when bot leaves/is removed
                    return self._handle_leave(data)
                else:
                    return jsonify({"status": "unknown_event"}), 400
            except Exception as e:
                logger.error(f"Error handling webhook: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/send_message', methods=['POST'])
        def send_message():
            """API endpoint for sending messages to Meet"""
            try:
                data = request.json
                message = data.get('message')
                meet_id = data.get('meet_id')
                
                # Here we would use Meet Add-ons SDK to send message
                # For now, just log it
                logger.info(f"Sending message to meet {meet_id}: {message}")
                
                return jsonify({"status": "sent"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({"status": "healthy"}), 200

    def _handle_join(self, data):
        """Handle bot joining a meeting"""
        meet_id = data.get('meetId')
        logger.info(f"Bot joined meeting: {meet_id}")
        return jsonify({"status": "joined"}), 200

    def _handle_message(self, data):
        """Handle incoming messages/questions"""
        meet_id = data.get('meetId')
        message = data.get('message')
        sender = data.get('sender')
        
        logger.info(f"Message from {sender} in {meet_id}: {message}")
        
        # Here we would:
        # 1. Process the message through our RAG pipeline
        # 2. Generate response using LLM
        # 3. Convert to speech using TTS
        # 4. Send back through Meet Add-ons SDK
        
        return jsonify({"status": "received"}), 200

    def _handle_leave(self, data):
        """Handle bot leaving a meeting"""
        meet_id = data.get('meetId')
        logger.info(f"Bot left meeting: {meet_id}")
        return jsonify({"status": "left"}), 200

    def start(self):
        """Start the server"""
        logger.info(f"Starting Meet bot server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)

    def start_async(self):
        """Start server in a separate thread"""
        thread = Thread(target=self.start)
        thread.daemon = True
        thread.start()
        return thread

# Initialize the app for Vercel
app = Flask(__name__)
CORS(app)
server = MeetBotServer()
server.setup_routes()

# For local development
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    server.start()