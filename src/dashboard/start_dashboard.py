# Dashboard launcher script
import webbrowser
import time
import os
import sys
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print("\n" + "="*70)
print("GOOGLE MEET BOT WITH DASHBOARD")
print("="*70)

print("\nStarting dashboard server...")
print("Please wait...")

dashboard_path = Path(__file__).parent / "dashboard.html"
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

from dashboard.dashboard_server import dashboard
dashboard.start()