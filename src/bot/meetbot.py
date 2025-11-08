# Google Meet bot with AI voice responses and vector search integration

import time
import threading
import speech_recognition as sr
from bot.audio_handler import AudioHandler
from bot.meet_controller import MeetController
from bot.ai_responder import AIResponder
from bot.fast_local_search import get_searcher  

from bot.chat_sender import MeetChatSender


class EdgeMeetBot:
    """Main bot orchestrator integrating audio, AI, and meeting control"""
    
    def __init__(self):
        self.profile_dir = MeetController.get_profile_dir()
        self.meet_controller = MeetController(self.profile_dir)
        self.audio_handler = AudioHandler()
        self.ai_responder = AIResponder()
        self.chat_sender = None
        self.listening = False
        self.wake_word = "okay assistant"  # Bot only responds when hearing this
    
    @property
    def driver(self):
        """Provide access to driver for compatibility"""
        return self.meet_controller.driver
    
    @property
    def recognizer(self):
        """Provide access to recognizer for compatibility"""
        return self.audio_handler.recognizer
    
    def _check_wake_word(self, text):
        """Check if text starts with wake word and extract the question"""
        text_lower = text.lower().strip()
        
        # Support multiple wake word variations for better recognition
        wake_words = [
            self.wake_word,           # Primary: "okay assistant"
            "ok assistant",           # Variation of okay
            "okay system",            # Alternative
            "ok system"               # Short version
        ]
        
        for wake in wake_words:
            if text_lower.startswith(wake):
                # Remove wake word and return the actual question
                question = text[len(wake):].strip()
                return True, question
        
        return False, None
    
    def start(self, meet_url):
        """Start the bot and join meeting"""
        try:
            self.meet_controller.setup_driver()
            self.meet_controller.check_login()
            self.meet_controller.set_virtual_microphone()
            self.meet_controller.join_meeting(meet_url)
            
            vector_searcher = get_searcher()
            self.ai_responder.set_vector_searcher(vector_searcher)
            
            self.chat_sender = MeetChatSender(self.driver)
            
            self.meet_controller.inject_virtual_mic_stream()
            time.sleep(2)
            
            time.sleep(3)
            self.speak("Hello, I'm your assistant for today. You can ask me questions by mentioning me, Okay assistant, at the start of your sentence.")
            
            print("Bot is running. Press Ctrl+C to exit...")
            print("Listening for speech from other participants...\n")
            
            self.listening = True
            listen_thread = threading.Thread(target=self._listen_continuously, daemon=True)
            listen_thread.start()
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nLeaving meeting...")
                self.listening = False
                self.stop()
                
        except Exception as e:
            print(f"\nError: {str(e)}")
            self.stop()
            raise
    
    def _listen_continuously(self):
        """Listen for audio from meeting and convert to text"""
        with sr.Microphone() as source:
            self.audio_handler.setup_recognizer(source)
            
            consecutive_silence = 0
            max_consecutive_silence = 1
            last_user_text = None
            
            while self.listening:
                try:
                    text = self.audio_handler.listen_for_speech(source)
                    
                    if text:
                        if self.audio_handler.bot_speaking:
                            self.audio_handler.stop_speaking()
                            time.sleep(0.5)
                        
                        # Check for wake word
                        has_wake_word, question = self._check_wake_word(text)
                        
                        if has_wake_word:
                            print(f"User asked: {question}")
                            last_user_text = question
                            consecutive_silence = 0
                        else:
                            last_user_text = None
                            consecutive_silence = 0
                    else:
                        consecutive_silence += 1
                        
                        if consecutive_silence >= max_consecutive_silence:
                            if last_user_text:
                                ai_response, citations = self.ai_responder.generate_response(last_user_text)
                                
                                # Add mention of links if there are citations
                                if citations:
                                    ai_response += " I've added some reference links in the chat for you."
                                
                                # Send citations to chat WHILE speaking (parallel processing)
                                if citations and self.chat_sender:
                                    # Start citation sending in background thread
                                    citation_thread = threading.Thread(
                                        target=self._send_citations_async,
                                        args=(citations,)
                                    )
                                    citation_thread.daemon = True
                                    citation_thread.start()
                                
                                # Speak the answer (citations are being sent in parallel)
                                self.speak(ai_response)
                                
                                last_user_text = None
                            consecutive_silence = 0
                    
                except Exception as e:
                    if self.listening:
                        print(f"Listening error: {str(e)}")
                    time.sleep(1)
    
    def _send_citations_async(self, citations):
        """Send citations to chat in background (async)"""
        try:
            self.chat_sender.send_citations(citations)
        except Exception as e:
            print(f"Error sending citations: {e}")
    
    def speak(self, text):
        """Convert text to speech and play to meeting"""
        self.meet_controller.ensure_mic_on()
        time.sleep(0.3)
        self.audio_handler.speak(text)
    
    def stop(self):
        """Stop the bot and clean up"""
        self.meet_controller.leave_meeting()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("Google Meet Bot - Edge Edition")
    print("="*50 + "\n")
    
    meet_url = input("Enter Google Meet URL: ")
    bot = EdgeMeetBot()
    
    try:
        bot.start(meet_url)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        bot.stop()
