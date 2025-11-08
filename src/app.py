# ================================================================
# Google Meet Bot - Main Entry Point
# ================================================================
# This file starts the dashboard server and opens the control panel
# ================================================================

import webbrowser
import time
import os
import sys
from pathlib import Path

print("\n" + "="*70)
print("GOOGLE MEET BOT - DASHBOARD")
print("="*70)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print("\nStarting dashboard server...")
print("Please wait...")

# Get dashboard HTML path
dashboard_path = Path(__file__).parent / "dashboard" / "dashboard.html"
dashboard_url = f"file:///{dashboard_path.as_posix()}"

print(f"\nDashboard: {dashboard_url}")
print("\nOpening dashboard in browser...")

time.sleep(1)
webbrowser.open(dashboard_url)

print("\n" + "="*70)
print("DASHBOARD SERVER RUNNING")
print("="*70)
print("\nDashboard opened in your browser")
print("WebSocket server running on ws://localhost:8765")
print("\nKeep this terminal running!")
print("Press Ctrl+C to stop the server")
print("\n" + "="*70 + "\n")

# Import and start dashboard server
from dashboard.dashboard_server import dashboard
dashboard.start()
