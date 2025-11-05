from playwright.sync_api import sync_playwright
import os
import time
from dotenv import load_dotenv

load_dotenv()

class GoogleMeetBot:
    def __init__(self, display_name="fastn-bot", user_data_dir=None):
        self.browser = None
        self.context = None
        self.page = None
        self.meet_url = None
        self.display_name = display_name
        self.user_data_dir = user_data_dir  # Chrome profile directory

    def start(self, meet_url):
        """Start the browser and join the meeting"""
        self.meet_url = meet_url
        
        playwright = sync_playwright().start()
        launch_args = {
            'headless': False,  # Set to True for production
            'args': [
                '--use-fake-ui-for-media-stream',  # Automatically allow camera/mic permissions
                '--use-fake-device-for-media-stream',  # Use fake audio/video streams
            ]
        }
        
        # Use existing Chrome profile if provided
        if self.user_data_dir:
            launch_args['executable_path'] = 'chrome'  # Use system Chrome
            launch_args['args'].extend([
                f'--user-data-dir={self.user_data_dir}',
                '--no-first-run',
                '--no-default-browser-check',
                '--password-store=basic'
            ])
            self.browser = playwright.chromium.launch(**launch_args)
        else:
            self.browser = playwright.chromium.launch(**launch_args)
        
        # Create a new context with permissions and media settings
        self.context = self.browser.new_context(
            permissions=['microphone', 'camera'],
            locale='en-US'
        )
        
        self.page = self.context.new_page()
        
        # Navigate to Google Meet
        print(f"Joining meeting: {meet_url}")
        self.page.goto(meet_url)
        
        # Wait for the page to load
        self.page.wait_for_load_state('networkidle')
        
        # Check if we can't join the meeting
        error_messages = [
            "You can't join this call",
            "You can't join this video call",
            "Meeting not found",
            "Invalid meeting code",
            "This meeting has ended",
            "You're not allowed to join this meeting"
        ]
        
        # Wait a moment for any error messages to appear
        self.page.wait_for_timeout(2000)
        
        # Check for error messages
        for error in error_messages:
            if self.page.get_by_text(error, exact=True).count() > 0:
                raise Exception(f"Cannot join meeting: {error}")
                
        # Check if we're actually on the meeting page by looking for common elements
        try:
            self.page.wait_for_selector('[data-meeting-title]', timeout=5000)
        except:
            raise Exception("This doesn't appear to be a valid Google Meet page")
        
        # Set display name if the input field is present
        name_input = self.page.get_by_label("Enter your name")
        if name_input.count() > 0:
            name_input.fill(self.display_name)
            print(f"Set display name to: {self.display_name}")
        
        # Turn off camera and microphone before joining
        self._handle_media_buttons()
        
        # Join the meeting
        self._join_meeting()
        
        print("Successfully joined the meeting!")
        
        # Keep the bot running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Leaving meeting...")
            self.stop()

    def _handle_media_buttons(self):
        """Turn off camera and microphone"""
        # Wait for media buttons to be available
        self.page.wait_for_selector('button[aria-label*="Turn off camera"]', timeout=5000)
        self.page.wait_for_selector('button[aria-label*="Turn off microphone"]', timeout=5000)
        
        # Turn off camera if it's on
        camera_button = self.page.locator('button[aria-label*="camera"]').first
        if 'Turn off camera' in camera_button.get_attribute('aria-label'):
            camera_button.click()
            print("Camera turned off")
            
        # Turn off microphone if it's on
        mic_button = self.page.locator('button[aria-label*="microphone"]').first
        if 'Turn off microphone' in mic_button.get_attribute('aria-label'):
            mic_button.click()
            print("Microphone turned off")

    def _join_meeting(self):
        """Click the join button"""
        # Look for the "Join now" or "Ask to join" button
        join_button = self.page.get_by_role("button", name="Join now")
        ask_to_join_button = self.page.get_by_role("button", name="Ask to join")
        
        if join_button.count() > 0:
            join_button.click()
            print("Clicked 'Join now'")
        elif ask_to_join_button.count() > 0:
            ask_to_join_button.click()
            print("Clicked 'Ask to join'")
        else:
            raise Exception("Could not find join button")

    def stop(self):
        """Leave the meeting and close the browser"""
        if self.page:
            # Click the leave call button
            leave_button = self.page.locator('button[aria-label*="Leave call"]')
            if leave_button:
                leave_button.click()
            
            self.page.close()
        
        if self.context:
            self.context.close()
        
        if self.browser:
            self.browser.close()

def get_chrome_profile_dir():
    """Get the default Chrome user data directory"""
    if os.name == 'nt':  # Windows
        return os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
    elif os.name == 'posix':  # Linux/Mac
        if os.path.exists(os.path.expanduser('~/.config/google-chrome')):
            return os.path.expanduser('~/.config/google-chrome')
        else:
            return os.path.expanduser('~/Library/Application Support/Google/Chrome')
    return None

if __name__ == "__main__":
    # Example usage
    meet_url = input("Enter Google Meet URL: ")
    
    # Get Chrome profile directory
    chrome_profile = get_chrome_profile_dir()
    if not chrome_profile:
        print("Warning: Could not find Chrome profile directory")
    
    # Create bot with Chrome profile
    bot = GoogleMeetBot(user_data_dir=chrome_profile)
    
    try:
        print("Using Chrome profile from:", chrome_profile)
        bot.start(meet_url)
    except Exception as e:
        print(f"\nError: {str(e)}")
        if "net::ERR_NETWORK_CHANGED" in str(e):
            print("Network connection error. Please check your internet connection.")
        elif "net::ERR_NAME_NOT_RESOLVED" in str(e):
            print("DNS error. Please check your internet connection.")
        elif "DisconnectedError" in str(e):
            print("Connection lost. Make sure you're logged into your Google account in Chrome.")
        bot.stop()
    except KeyboardInterrupt:
        print("\nExiting...")
        bot.stop()