"""
JavaScript Script Loader for Meet Controller
Centralizes all JavaScript code in separate .js files for better maintainability
"""

import os
from pathlib import Path


class ScriptLoader:
    """Load JavaScript files from the scripts directory"""
    
    def __init__(self):
        self.scripts_dir = Path(__file__).parent / 'scripts'
        self._script_cache = {}
    
    def load(self, script_name):
        """
        Load a JavaScript file by name
        
        Args:
            script_name: Name of the .js file (without extension)
            
        Returns:
            str: JavaScript code as string
        """
        # Check cache first
        if script_name in self._script_cache:
            return self._script_cache[script_name]
        
        script_path = self.scripts_dir / f"{script_name}.js"
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Cache for future use
        self._script_cache[script_name] = script_content
        
        return script_content
    
    def execute(self, driver, script_name):
        """
        Load and execute a JavaScript file
        
        Args:
            driver: Selenium WebDriver instance
            script_name: Name of the .js file (without extension)
            
        Returns:
            Any: Result from JavaScript execution
        """
        script = self.load(script_name)
        return driver.execute_script(script)


# Singleton instance
_loader = None

def get_script_loader():
    """Get the singleton ScriptLoader instance"""
    global _loader
    if _loader is None:
        _loader = ScriptLoader()
    return _loader
