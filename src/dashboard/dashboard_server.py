# WebSocket dashboard server for monitoring and controlling the bot
import asyncio
import websockets
import json
import threading
import queue
from datetime import datetime

class DashboardServer:
    def __init__(self):
        self.clients = set()
        self.log_queue = queue.Queue()
        self.bot_instance = None
        self.running = False
        
    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"[Dashboard] Client connected. Total clients: {len(self.clients)}")
        
    async def unregister(self, websocket):
        self.clients.remove(websocket)
        print(f"[Dashboard] Client disconnected. Total clients: {len(self.clients)}")
        
    async def send_to_all(self, message):
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
    
    def log(self, message, level='info'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_data = {
            'type': 'log',
            'message': message,
            'level': level,
            'timestamp': timestamp
        }
        self.log_queue.put(log_data)
        print(f"[{timestamp}] {message}")
        
    def update_status(self, status):
        self.log_queue.put({
            'type': 'status',
            'status': status
        })
        
    def message_sent(self):
        self.log_queue.put({
            'type': 'message_sent'
        })
        
    def user_message(self):
        self.log_queue.put({
            'type': 'user_message'
        })
        
    async def process_queue(self):
        while self.running:
            try:
                if not self.log_queue.empty():
                    message = self.log_queue.get_nowait()
                    await self.send_to_all(message)
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[Dashboard] Queue processing error: {e}")
                
    async def handle_client(self, websocket):
        await self.register(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    action = data.get('action')
                    
                    if action == 'start':
                        meet_url = data.get('url')
                        self.log(f"Starting bot for: {meet_url}", 'info')
                        
                        if not self.bot_instance or not hasattr(self.bot_instance, 'driver'):
                            bot_thread = threading.Thread(
                                target=self.run_bot_wrapper,
                                args=(meet_url,),
                                daemon=True
                            )
                            bot_thread.start()
                        else:
                            self.log("Bot is already running!", 'warning')
                            
                    elif action == 'stop':
                        self.log("Stopping bot...", 'warning')
                        if self.bot_instance:
                            self.bot_instance.stop()
                            self.bot_instance = None
                            self.update_status('idle')
                            self.log("Bot stopped", 'success')
                        
                except json.JSONDecodeError:
                    self.log("Invalid message format", 'error')
                except Exception as e:
                    self.log(f"Error handling message: {str(e)}", 'error')
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
            
    def run_bot_wrapper(self, meet_url):
        import sys
        import os
        import builtins
        original_print = builtins.print
        
        try:
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(current_dir)
            sys.path.insert(0, src_dir)
            
            from bot.meetbot import EdgeMeetBot
            
            def dashboard_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                
                level = 'info'
                if '✅' in message or 'Successfully' in message or 'success' in message.lower():
                    level = 'success'
                    message = message.replace('✅', '').strip()
                elif '❌' in message or 'Error' in message or 'error' in message.lower():
                    level = 'error'
                    message = message.replace('❌', '').strip()
                elif '⚠️' in message or 'Warning' in message or 'warning' in message.lower():
                    level = 'warning'
                    message = message.replace('⚠️', '').strip()
                elif '🗣️' in message or 'Bot speaking' in message:
                    level = 'speaking'
                    message = message.replace('🗣️', '').strip()
                elif '👤' in message or 'User said' in message:
                    level = 'user'
                    message = message.replace('👤', '').strip()
                
                import re
                message = re.sub(r'[🤖📹🔗🎯⏳🎮🔍🚀🎤🔊📊🎧💬🔁⏹️✅❌⚠️🗣️👤📋🔌🔄]', '', message).strip()
                
                if message and not message.startswith('['):  # Avoid duplicate timestamps
                    self.log(message, level)
                
                original_print(*args, **kwargs)
            
            builtins.print = dashboard_print
            
            self.log("Initializing bot...", 'info')
            self.update_status('running')
            
            bot = EdgeMeetBot()
            self.bot_instance = bot
            
            original_speak = bot.speak
            def speak_with_counting(text):
                self.message_sent()
                return original_speak(text)
            bot.speak = speak_with_counting
            
            original_recognize = bot.recognizer.recognize_google
            def recognize_with_counting(audio, *args, **kwargs):
                result = original_recognize(audio, *args, **kwargs)
                if result and result.strip():
                    self.user_message()
                return result
            bot.recognizer.recognize_google = recognize_with_counting
            
            self.log("Bot initialized successfully", 'success')
            
            bot.start(meet_url)
            
        except KeyboardInterrupt:
            self.log("Bot stopped by user", 'warning')
            self.update_status('idle')
        except Exception as e:
            self.log(f"Bot error: {str(e)}", 'error')
            self.update_status('error')
            import traceback
            traceback.print_exc()
        finally:
            builtins.print = original_print
            self.bot_instance = None
            self.update_status('idle')
            
    async def start_server(self):
        self.running = True
        
        asyncio.create_task(self.process_queue())
        
        async with websockets.serve(self.handle_client, "localhost", 8765):
            self.log("Dashboard server started on ws://localhost:8765", 'success')
            self.log("Open dashboard.html in your browser", 'info')
            await asyncio.Future()
            
    def start(self):
        try:
            asyncio.run(self.start_server())
        except KeyboardInterrupt:
            print("\n[Dashboard] Server stopped")
            self.running = False

dashboard = DashboardServer()

if __name__ == "__main__":
    print("="*60)
    print("Google Meet Bot Dashboard Server")
    print("="*60)
    print("\nInstructions:")
    print("1. Keep this terminal running")
    print("2. Open 'dashboard.html' in your browser")
    print("3. Enter meeting link and click Start")
    print("\n" + "="*60 + "\n")
    
    dashboard.start()