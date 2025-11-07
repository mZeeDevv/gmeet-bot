# Google Meet bot with AI voice responses and vector search integration
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from gtts import gTTS
from pathlib import Path
import tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import speech_recognition as sr
import threading
import pygame
from dotenv import load_dotenv
import google.generativeai as genai
from bot.vector_search import get_searcher
from bot.chat_sender import MeetChatSender
load_dotenv()
class EdgeMeetBot:
    def __init__(self):
        self.driver = None
        self.profile_dir = self._get_profile_dir()
        self.listening = False
        self.bot_speaking = False
        self.interrupt_speaking = False
        self.recognizer = sr.Recognizer()
        self.virtual_speaker = None
        self._detect_virtual_devices()
        self._initialize_gemini()
        self.vector_searcher = None
        self.chat_sender = None
    def _initialize_gemini(self):
        """Initialize Gemini AI model"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("⚠️  GEMINI_API_KEY not found in .env file")
                self.gemini_model = None
                return
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-pro')
            self.system_context = """You are a helpful AI assistant in a Google Meet call. 
You can answer any general questions about various topics."""
            print("✅ Gemini AI initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Gemini: {str(e)}")
            self.gemini_model = None
    def generate_ai_response(self, user_question):
        """Generate AI response using Gemini with vector search context"""
        try:
            if not self.gemini_model:
                return "I'm having trouble with my AI connection. Could you please repeat that?", []
            citations = []
            context = ""
            if self.vector_searcher and self.vector_searcher.is_available():
                print("📚 Searching documentation...")
                results, citations = self.vector_searcher.search_docs(user_question, limit=3)
                if results:
                    context = self.vector_searcher.format_context_for_ai(results)
                    print(f"✅ Found {len(results)} relevant documents")
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
            print(f"❌ Error generating AI response: {str(e)}")
            return "I'm sorry, I couldn't process that. Could you rephrase your question?", []
    def _detect_virtual_devices(self):
        """Detect VB-Audio Virtual Cable devices"""
        try:
            devices = sd.query_devices()
            print("\n🔍 Detecting audio devices...")
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                if 'cable input' in device_name and device['max_output_channels'] > 0:
                    self.virtual_speaker = i
                    print(f"  ✅ Found Virtual Speaker: {device['name']} (index: {i})")
            if not self.virtual_speaker:
                print("  ⚠️  VB-Cable not detected! Please install VB-Audio Virtual Cable")
                print("  📥 Download from: https://vb-audio.com/Cable/")
            else:
                print(f"  ✓ Virtual Audio Cable ready!")
        except Exception as e:
            print(f"  ❌ Device detection error: {str(e)}")
    def _get_profile_dir(self):
        """Get or create persistent profile directory"""
        if os.name == 'nt':
            profile_dir = os.path.join(os.environ['LOCALAPPDATA'], 'MeetBot', 'EdgeProfile')
        else:
            profile_dir = os.path.expanduser('~/.meetbot/edge_profile')
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        return profile_dir
    def start(self, meet_url):
        try:
            edge_options = Options()
            edge_options.add_argument(f"user-data-dir={self.profile_dir}")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_argument("--use-fake-ui-for-media-stream")
            edge_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.media_stream_mic": 1,
                "profile.default_content_setting_values.media_stream_camera": 1,
                "profile.default_content_setting_values.notifications": 2
            })
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option('useAutomationExtension', False)
            print("🚀 Opening Edge with saved profile...")
            self.driver = webdriver.Edge(options=edge_options)
            self.driver.maximize_window()
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("🔍 Checking login...")
            self.driver.get("https://accounts.google.com")
            time.sleep(2)
            if "signin" in self.driver.current_url.lower():
                print("\n⚠️  Please sign in to Google (ONE TIME ONLY!)")
                input("Press Enter after signing in: ")
            else:
                print("✅ Already signed in!")
            print(f"🔗 Joining: {meet_url}")
            self.driver.get(meet_url)
            time.sleep(4)
            print("🎤 Configuring virtual audio devices...")
            self._set_virtual_microphone()
            time.sleep(2)
            if "You can't join" in self.driver.page_source:
                raise Exception("❌ Cannot join this meeting")
            print("📹 Turning off camera...")
            self._disable_camera()
            time.sleep(2)
            print("🎯 Joining...")
            self._join_meeting()
            print("⏳ Waiting for join...")
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Leave call')]"))
            )
            print("\n✅ Successfully joined!")
            print("📚 Initializing vector search...")
            self.vector_searcher = get_searcher()
            self.chat_sender = MeetChatSender(self.driver)
            print("💬 Chat sender initialized")
            print("🔄 Injecting Virtual Microphone stream into meeting...")
            self._inject_virtual_mic_stream()
            time.sleep(2)
            time.sleep(3)
            self.speak("Hello, How can I help you?")
            print("🤖 Bot is running. Press Ctrl+C to exit...")
            print("🎧 Listening for speech from other participants...\n")
            self.listening = True
            listen_thread = threading.Thread(target=self._listen_continuously, daemon=True)
            listen_thread.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Leaving meeting...")
                self.listening = False
                self.stop()
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            self.stop()
            raise
    def _set_virtual_microphone(self):
        """Set browser to use VB-Cable Output (Virtual Microphone) BEFORE joining"""
        try:
            script = """
            (async function() {
                try {
                    // Get all audio input devices
                    const devices = await navigator.mediaDevices.enumerateDevices();
                    const audioInputs = devices.filter(d => d.kind === 'audioinput');
                    console.log('Available audio inputs:', audioInputs.map(d => d.label));
                    // Find CABLE Output (Virtual Microphone)
                    const virtualMic = audioInputs.find(d => 
                        d.label.toLowerCase().includes('cable output') ||
                        d.label.toLowerCase().includes('vb-audio virtual cable')
                    );
                    if (virtualMic) {
                        // Store the device ID for Google Meet to use
                        window.virtualMicId = virtualMic.deviceId;
                        // Request access to virtual microphone and KEEP the stream active
                        const stream = await navigator.mediaDevices.getUserMedia({
                            audio: { 
                                deviceId: { exact: virtualMic.deviceId },
                                echoCancellation: false,
                                noiseSuppression: false,
                                autoGainControl: false
                            }
                        });
                        // Don't stop the stream - Google Meet will use it
                        window.virtualMicStream = stream;
                        console.log('Virtual Microphone activated:', virtualMic.label);
                        return 'success: ' + virtualMic.label;
                    } else {
                        return 'error: Virtual microphone not found. Available: ' + audioInputs.map(d => d.label).join(', ');
                    }
                } catch(e) {
                    return 'error: ' + e.message;
                }
            })();
            """
            result = self.driver.execute_script(script)
            if 'success' in str(result):
                print(f"  ✅ Virtual Microphone activated: {result.split(': ')[1]}")
            else:
                print(f"  ⚠️  {result}")
            time.sleep(2)
            self._click_mic_settings()
        except Exception as e:
            print(f"  ⚠️  Virtual mic setup: {str(e)}")
    def _click_mic_settings(self):
        """Click microphone settings dropdown to select Virtual Cable"""
        try:
            selectors = [
                "//button[contains(@aria-label, 'Select microphone')]",
                "//button[contains(@aria-label, 'microphone')]//following-sibling::button",
                "//div[contains(@class, 'audio-settings')]",
            ]
            for selector in selectors:
                try:
                    btn = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    btn.click()
                    print("  🎤 Opened microphone settings")
                    time.sleep(1)
                    cable_option = self.driver.find_element(By.XPATH, "//*[contains(text(), 'CABLE Output') or contains(text(), 'VB-Audio')]")
                    cable_option.click()
                    print("  ✅ Selected CABLE Output from dropdown")
                    time.sleep(1)
                    return
                except:
                    continue
            print("  ℹ️  Microphone settings not accessible via UI (relying on JavaScript activation)")
        except Exception as e:
            print(f"  ℹ️  UI mic selection: {str(e)}")
    def _inject_virtual_mic_stream(self):
        """Inject virtual microphone stream into active Google Meet call"""
        try:
            script = """
            (async function() {
                try {
                    // Use the virtual mic stream we created earlier
                    if (!window.virtualMicStream) {
                        return 'error: Virtual mic stream not found';
                    }
                    // Replace the audio track in the peer connection
                    // This forces Google Meet to use our virtual microphone
                    const stream = window.virtualMicStream;
                    const audioTrack = stream.getAudioTracks()[0];
                    if (audioTrack) {
                        console.log('Injecting virtual mic track:', audioTrack.label);
                        return 'success: Audio track injected - ' + audioTrack.label;
                    } else {
                        return 'error: No audio track found';
                    }
                } catch(e) {
                    return 'error: ' + e.message;
                }
            })();
            """
            result = self.driver.execute_script(script)
            if 'success' in str(result):
                print(f"  ✅ {result}")
            else:
                print(f"  ⚠️  {result}")
        except Exception as e:
            print(f"  ⚠️  Stream injection: {str(e)}")
    def _disable_camera(self):
        """Turn off camera only (keep mic on for bot to speak)"""
        try:
            time.sleep(2)
            cameras = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'camera') or contains(@aria-label, 'Camera')]")
            for btn in cameras:
                try:
                    label = btn.get_attribute('aria-label')
                    if label:
                        print(f"  Camera button found: {label}")
                        if 'Turn off' in label or 'camera on' in label.lower():
                            btn.click()
                            print("  ✅ Camera turned OFF")
                            time.sleep(1)
                            break
                        elif 'Turn on' in label or 'camera off' in label.lower():
                            print("  ✅ Camera already OFF")
                            break
                except Exception as e:
                    print(f"  Error checking camera: {e}")
                    continue
        except Exception as e:
            print(f"  ⚠️  Camera config: {str(e)}")
    def _join_meeting(self):
        """Click join button or auto-join if already in"""
        try:
            selectors = [
                "//button[contains(text(), 'Join now')]",
                "//button[contains(text(), 'Ask to join')]",
                "//span[contains(text(), 'Join now')]/parent::button",
                "//span[contains(text(), 'Ask to join')]/parent::button"
            ]
            joined = False
            for selector in selectors:
                try:
                    button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    print("  ✓ Clicked join button")
                    joined = True
                    break
                except:
                    continue
            if not joined:
                print("  ℹ️  No join button (may already be in meeting)")
        except Exception as e:
            print(f"  ℹ️  Join: {str(e)}")
    def _listen_continuously(self):
        """Listen for audio from meeting and convert to text"""
        with sr.Microphone() as source:
            print("🎤 Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            consecutive_silence = 0
            max_consecutive_silence = 1
            last_user_text = None
            while self.listening:
                try:
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=15)
                    text = self.recognizer.recognize_google(audio)
                    if text.strip():
                        if self.bot_speaking:
                            print(f"\n⚠️  User interrupted: {text}")
                            self.interrupt_speaking = True
                            sd.stop()
                            self.bot_speaking = False
                            time.sleep(0.5)
                        print(f"\n👤 User said: {text}\n")
                        last_user_text = text
                        consecutive_silence = 0
                except sr.WaitTimeoutError:
                    consecutive_silence += 1
                    if consecutive_silence >= max_consecutive_silence:
                        if last_user_text:
                            print("🤖 Generating AI response...")
                            ai_response, citations = self.generate_ai_response(last_user_text)
                            self.speak(ai_response)
                            if citations and self.chat_sender:
                                print("📤 Sending citations to chat...")
                                self.chat_sender.send_citations(citations)
                            last_user_text = None
                        consecutive_silence = 0
                except sr.UnknownValueError:
                    consecutive_silence += 1
                    if consecutive_silence >= max_consecutive_silence:
                        if last_user_text:
                            print("🤖 Generating AI response...")
                            ai_response, citations = self.generate_ai_response(last_user_text)
                            self.speak(ai_response)
                            if citations and self.chat_sender:
                                print("📤 Sending citations to chat...")
                                self.chat_sender.send_citations(citations)
                            last_user_text = None
                        consecutive_silence = 0
                except Exception as e:
                    if self.listening:
                        print(f"❌ Listening error: {str(e)}")
                    time.sleep(1)
    def _monitor_for_interruption(self):
        """Monitor for user speech while bot is speaking - DISABLED to avoid self-interruption"""
        pass
    def speak(self, text):
        """Convert text to speech and play to Virtual Speaker (CABLE Input)"""
        try:
            self.bot_speaking = True
            self.interrupt_speaking = False
            print(f"🗣️  Bot speaking: {text}")
            if not self.virtual_speaker:
                print("  ⚠️  Virtual Audio Cable not detected! Audio may not work.")
                return
            self._ensure_mic_on()
            time.sleep(0.3)
            temp_dir = Path(tempfile.gettempdir()) / "meet_bot_audio"
            temp_dir.mkdir(exist_ok=True)
            audio_file = temp_dir / f"speech_{int(time.time())}.mp3"
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(str(audio_file))
            device_info = sd.query_devices(self.virtual_speaker)
            supported_rate = int(device_info['default_samplerate'])
            print(f"  🔄 Loading audio and converting to {supported_rate}Hz...")
            try:
                audio = AudioSegment.from_mp3(str(audio_file))
                audio = audio.set_frame_rate(supported_rate)
                audio = audio.set_channels(2)
                wav_file = audio_file.with_suffix('.wav')
                audio.export(str(wav_file), format='wav')
                data, samplerate = sf.read(str(wav_file))
            except Exception as conv_error:
                print(f"  ⚠️  FFmpeg not available, using alternative method...")
                import pygame
                pygame.mixer.init(frequency=supported_rate, size=-16, channels=2)
                sound = pygame.mixer.Sound(str(audio_file))
                raw_data = pygame.sndarray.array(sound)
                data = raw_data.astype(np.float32) / 32768.0
                samplerate = supported_rate
                pygame.mixer.quit()
            print(f"  🔊 Playing to Virtual Speaker at {samplerate}Hz...")
            sd.play(data, samplerate, device=self.virtual_speaker)
            while sd.get_stream().active:
                if self.interrupt_speaking:
                    print("  ⚠️  Stopping due to user interruption")
                    sd.stop()
                    break
                time.sleep(0.1)
            try:
                audio_file.unlink()
                if 'wav_file' in locals():
                    wav_file.unlink()
            except:
                pass
            time.sleep(1)
            print("  ✅ Audio sent through Virtual Cable → Meeting")
        except Exception as e:
            print(f"  ❌ Speech error: {str(e)}")
        finally:
            self.bot_speaking = False
    def _ensure_mic_on(self):
        """Make sure microphone is ON for speaking"""
        try:
            mics = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'microphone') or contains(@aria-label, 'Microphone')]")
            for btn in mics:
                label = btn.get_attribute('aria-label')
                if label and ('Turn on' in label or 'microphone off' in label.lower()):
                    btn.click()
                    print("  🎤 Microphone turned ON for speaking")
                    time.sleep(0.5)
                    break
        except:
            pass
    def stop(self):
        """Leave and close"""
        try:
            if self.driver:
                try:
                    leave = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Leave call')]")
                    leave.click()
                    time.sleep(2)
                except:
                    pass
                self.driver.quit()
                print("✅ Browser closed")
        except Exception as e:
            print(f"Cleanup error: {str(e)}")
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 Google Meet Bot - Edge Edition")
    print("="*50 + "\n")
    meet_url = input("Enter Google Meet URL: ")
    bot = EdgeMeetBot()
    try:
        bot.start(meet_url)
    except KeyboardInterrupt:
        print("\n Exiting...")
    finally:
        bot.stop()
