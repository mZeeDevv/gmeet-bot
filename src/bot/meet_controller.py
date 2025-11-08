# Google Meet browser control and navigation

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


class MeetController:
    """Controls Google Meet browser interactions"""
    
    def __init__(self, profile_dir):
        self.driver = None
        self.profile_dir = profile_dir
    
    @staticmethod
    def get_profile_dir():
        """Get or create persistent profile directory"""
        if os.name == 'nt':
            profile_dir = os.path.join(os.environ['LOCALAPPDATA'], 'MeetBot', 'EdgeProfile')
        else:
            profile_dir = os.path.expanduser('~/.meetbot/edge_profile')
        
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        
        return profile_dir
    
    def setup_driver(self):
        """Setup Edge browser with required options"""
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
        
        print("Opening Edge with saved profile...")
        self.driver = webdriver.Edge(options=edge_options)
        self.driver.maximize_window()
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def check_login(self):
        """Check if user is logged into Google"""
        print("Checking login...")
        self.driver.get("https://accounts.google.com")
        time.sleep(2)
        
        if "signin" in self.driver.current_url.lower():
            print("\nPlease sign in to Google (ONE TIME ONLY!)")
            input("Press Enter after signing in: ")
        else:
            print("Already signed in!")
    
    def join_meeting(self, meet_url):
        """Navigate to meeting and join"""
        print(f"Joining: {meet_url}")
        self.driver.get(meet_url)
        time.sleep(4)
        
        if "You can't join" in self.driver.page_source:
            raise Exception("Cannot join this meeting")
        
        print("Turning off camera...")
        self.disable_camera()
        time.sleep(2)
        
        print("Joining...")
        self.click_join_button()
        
        print("Waiting for join...")
        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Leave call')]"))
        )
        print("\nSuccessfully joined!")
    
    def disable_camera(self):
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
                            print("  Camera turned OFF")
                            time.sleep(1)
                            break
                        elif 'Turn on' in label or 'camera off' in label.lower():
                            print("  Camera already OFF")
                            break
                except Exception as e:
                    print(f"  Error checking camera: {e}")
                    continue
        except Exception as e:
            print(f"  Camera config: {str(e)}")
    
    def click_join_button(self):
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
                    print("  Clicked join button")
                    joined = True
                    break
                except:
                    continue
            
            if not joined:
                print("  No join button (may already be in meeting)")
        except Exception as e:
            print(f"  Join: {str(e)}")
    
    def set_virtual_microphone(self):
        """Set browser to use VB-Cable Output (Virtual Microphone) BEFORE joining"""
        try:
            print("Configuring virtual audio devices...")
            
            script = """
            (async function() {
                try {
                    const devices = await navigator.mediaDevices.enumerateDevices();
                    const audioInputs = devices.filter(d => d.kind === 'audioinput');
                    console.log('Available audio inputs:', audioInputs.map(d => d.label));
                    
                    const virtualMic = audioInputs.find(d => 
                        d.label.toLowerCase().includes('cable output') ||
                        d.label.toLowerCase().includes('vb-audio virtual cable')
                    );
                    
                    if (virtualMic) {
                        window.virtualMicId = virtualMic.deviceId;
                        const stream = await navigator.mediaDevices.getUserMedia({
                            audio: { 
                                deviceId: { exact: virtualMic.deviceId },
                                echoCancellation: false,
                                noiseSuppression: false,
                                autoGainControl: false
                            }
                        });
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
                print(f"  Virtual Microphone activated: {result.split(': ')[1]}")
            else:
                print(f"  {result}")
            
            time.sleep(2)
            self.click_mic_settings()
            
        except Exception as e:
            print(f"  Virtual mic setup: {str(e)}")
    
    def click_mic_settings(self):
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
                    print("  Opened microphone settings")
                    time.sleep(1)
                    
                    cable_option = self.driver.find_element(By.XPATH, "//*[contains(text(), 'CABLE Output') or contains(text(), 'VB-Audio')]")
                    cable_option.click()
                    print("  Selected CABLE Output from dropdown")
                    time.sleep(1)
                    return
                except:
                    continue
            
            print("  Microphone settings not accessible via UI (relying on JavaScript activation)")
        except Exception as e:
            print(f"  UI mic selection: {str(e)}")
    
    def inject_virtual_mic_stream(self):
        """Inject virtual microphone stream into active Google Meet call"""
        try:
            print("Injecting Virtual Microphone stream into meeting...")
            
            script = """
            (async function() {
                try {
                    if (!window.virtualMicStream) {
                        return 'error: Virtual mic stream not found';
                    }
                    
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
                print(f"  {result}")
            else:
                print(f"  {result}")
        except Exception as e:
            print(f"  Stream injection: {str(e)}")
    
    def ensure_mic_on(self):
        """Make sure microphone is ON for speaking"""
        try:
            mics = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'microphone') or contains(@aria-label, 'Microphone')]")
            
            for btn in mics:
                label = btn.get_attribute('aria-label')
                if label and ('Turn on' in label or 'microphone off' in label.lower()):
                    btn.click()
                    print("  Microphone turned ON for speaking")
                    time.sleep(0.5)
                    break
        except:
            pass
    
    def leave_meeting(self):
        """Leave the meeting and close browser"""
        try:
            if self.driver:
                try:
                    leave = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Leave call')]")
                    leave.click()
                    time.sleep(2)
                except:
                    pass
                
                self.driver.quit()
                print("Browser closed")
        except Exception as e:
            print(f"Cleanup error: {str(e)}")
