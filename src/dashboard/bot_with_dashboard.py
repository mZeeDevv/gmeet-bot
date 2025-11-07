# Bot integration with dashboard functionality
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.meetbot import EdgeMeetBot
from dashboard_server import dashboard

class DashboardBot(EdgeMeetBot):
    
    def __init__(self):
        super().__init__()
        self.dashboard = dashboard
        
    def log(self, message, level='info'):
        self.dashboard.log(message, level)
        
    def start(self, meet_url):
        try:
            self.log(" Opening Edge with saved profile...", 'info')
            super().start(meet_url)
        except Exception as e:
            self.log(f"❌ Error: {str(e)}", 'error')
            raise
            
    def speak(self, text):
        self.log(f" Bot speaking: {text}", 'speaking')
        self.dashboard.message_sent()
        super().speak(text)
        
    def _listen_continuously(self):
        self.log(" Listening for speech...", 'info')
        
        original_recognize = self.recognizer.recognize_google
        
        def recognize_with_logging(audio, *args, **kwargs):
            result = original_recognize(audio, *args, **kwargs)
            if result:
                self.log(f" User said: {result}", 'user')
                self.dashboard.user_message()
            return result
            
        self.recognizer.recognize_google = recognize_with_logging
        
        super()._listen_continuously()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  This file should be run through dashboard_server.py")
    print("="*60)
    print("\n Instructions:")
    print("1. Run: python src/dashboard_server.py")
    print("2. Open: src/dashboard.html in browser")
    print("3. Enter meeting link and start bot")
    print("\n" + "="*60 + "\n")