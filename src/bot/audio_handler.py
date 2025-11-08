# Audio handling for virtual devices, speech recognition, and text-to-speech

import sounddevice as sd
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import speech_recognition as sr
from gtts import gTTS
from pathlib import Path
import tempfile
import time
import pygame


class AudioHandler:
    """Handles audio input/output for the bot"""
    
    def __init__(self):
        self.virtual_speaker = None
        self.recognizer = sr.Recognizer()
        self.bot_speaking = False
        self.interrupt_speaking = False
        self._detect_virtual_devices()
    
    def _detect_virtual_devices(self):
        """Detect VB-Audio Virtual Cable devices"""
        try:
            devices = sd.query_devices()
            print("\nDetecting audio devices...")
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                if 'cable input' in device_name and device['max_output_channels'] > 0:
                    self.virtual_speaker = i
                    print(f"  Found Virtual Speaker: {device['name']} (index: {i})")
            if not self.virtual_speaker:
                print("  VB-Cable not detected! Please install VB-Audio Virtual Cable")
                print("  Download from: https://vb-audio.com/Cable/")
            else:
                print(f"  Virtual Audio Cable ready!")
        except Exception as e:
            print(f"  Device detection error: {str(e)}")
    
    def speak(self, text):
        """Convert text to speech and play to Virtual Speaker (CABLE Input)"""
        try:
            self.bot_speaking = True
            self.interrupt_speaking = False
            print(f"Bot speaking: {text}")
            
            if not self.virtual_speaker:
                print("  Virtual Audio Cable not detected! Audio may not work.")
                return
            
            temp_dir = Path(tempfile.gettempdir()) / "meet_bot_audio"
            temp_dir.mkdir(exist_ok=True)
            audio_file = temp_dir / f"speech_{int(time.time())}.mp3"
            
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(str(audio_file))
            
            device_info = sd.query_devices(self.virtual_speaker)
            supported_rate = int(device_info['default_samplerate'])
            print(f"  Loading audio and converting to {supported_rate}Hz...")
            
            try:
                audio = AudioSegment.from_mp3(str(audio_file))
                audio = audio.set_frame_rate(supported_rate)
                audio = audio.set_channels(2)
                wav_file = audio_file.with_suffix('.wav')
                audio.export(str(wav_file), format='wav')
                data, samplerate = sf.read(str(wav_file))
            except Exception as conv_error:
                print(f"  FFmpeg not available, using alternative method...")
                import pygame
                pygame.mixer.init(frequency=supported_rate, size=-16, channels=2)
                sound = pygame.mixer.Sound(str(audio_file))
                raw_data = pygame.sndarray.array(sound)
                data = raw_data.astype(np.float32) / 32768.0
                samplerate = supported_rate
                pygame.mixer.quit()
            
            print(f"  Playing to Virtual Speaker at {samplerate}Hz...")
            sd.play(data, samplerate, device=self.virtual_speaker)
            
            while sd.get_stream().active:
                if self.interrupt_speaking:
                    print("  Stopping due to user interruption")
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
            print("  Audio sent through Virtual Cable to Meeting")
            
        except Exception as e:
            print(f"  Speech error: {str(e)}")
        finally:
            self.bot_speaking = False
    
    def setup_recognizer(self, source):
        """Configure speech recognizer with microphone"""
        print("Adjusting for ambient noise...")
        self.recognizer.adjust_for_ambient_noise(source, duration=2)
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
    
    def listen_for_speech(self, source, timeout=2, phrase_time_limit=15):
        """Listen for speech and return recognized text"""
        try:
            audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = self.recognizer.recognize_google(audio)
            return text.strip() if text else None
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"Listening error: {str(e)}")
            return None
    
    def stop_speaking(self):
        """Stop current speech output"""
        self.interrupt_speaking = True
        sd.stop()
        self.bot_speaking = False
