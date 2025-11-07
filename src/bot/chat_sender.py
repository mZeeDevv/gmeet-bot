# Chat message sender for posting citations to Google Meet chat

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class MeetChatSender:
    def __init__(self, driver):
        self.driver = driver
        self.chat_opened = False
    
    @staticmethod
    def _sanitize_message(text: str) -> str:
        sanitized = ''.join(char for char in text if ord(char) < 0x10000)
        return sanitized
    
    def open_chat(self):
        try:
            if self.chat_opened:
                return True
            
            chat_selectors = [
                "//button[@aria-label='Chat with everyone']",
                "//button[contains(@aria-label, 'Chat')]",
                "//button[@data-tooltip='Chat with everyone']",
                "[aria-label*='Chat']",
                "button[jsname='A5il2e']"  # Google Meet specific
            ]
            
            for selector in chat_selectors:
                try:
                    if selector.startswith("//"):
                        chat_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        chat_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    chat_button.click()
                    print("💬 Chat panel opened")
                    time.sleep(1)
                    self.chat_opened = True
                    return True
                    
                except Exception:
                    continue
            
            print("⚠️  Could not find chat button")
            return False
            
        except Exception as e:
            print(f"❌ Error opening chat: {str(e)}")
            return False
    
    def send_message(self, message: str) -> bool:
        try:
            if not self.chat_opened:
                if not self.open_chat():
                    return False
            
            input_selectors = [
                "//textarea[@placeholder='Send a message to everyone']",
                "//textarea[@aria-label='Send a message to everyone']",
                "textarea[placeholder*='message']",
                "textarea[aria-label*='message']",
                "div[contenteditable='true']"
            ]
            
            chat_input = None
            for selector in input_selectors:
                try:
                    if selector.startswith("//"):
                        chat_input = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        chat_input = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    
                    if chat_input:
                        break
                except Exception:
                    continue
            
            if not chat_input:
                print("⚠️  Could not find chat input box")
                return False
            
            safe_message = self._sanitize_message(message)
            
            chat_input.click()
            time.sleep(0.3)
            chat_input.send_keys(safe_message)
            time.sleep(0.3)
            
            chat_input.send_keys(Keys.CONTROL + Keys.RETURN)
            time.sleep(0.5)
            
            print(f"Chat message sent: {safe_message[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error sending chat message: {str(e)}")
            return False
    
    def send_citations(self, citations: list) -> bool:
        if not citations:
            return False
        
        try:
            citations_text = "Sources:\n" + "\n".join([f"- {url}" for url in citations])
            
            return self.send_message(citations_text)
            
        except Exception as e:
            print(f"❌ Error sending citations: {str(e)}")
            return False
    
    def close_chat(self):
        try:
            if not self.chat_opened:
                return
            
            chat_button = self.driver.find_element(
                By.XPATH, 
                "//button[@aria-label='Chat with everyone']"
            )
            chat_button.click()
            self.chat_opened = False
            print("💬 Chat panel closed")
            
        except Exception as e:
            print(f"⚠️  Could not close chat: {str(e)}")