// Disable webdriver detection to avoid bot detection
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
