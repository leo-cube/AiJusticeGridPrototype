#!/usr/bin/env python3
"""
Simple web server to serve the Murder Agent UI
"""

import os
import http.server
import socketserver
import webbrowser
from pathlib import Path

# Configuration
PORT = 8080
DIRECTORY = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # Redirect root to login page
        if self.path == '/':
            self.path = '/login.html'
        super().do_GET()

def start_server():
    """Start the web server"""
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"Murder Agent UI Server starting...")
            print(f"Serving at: http://localhost:{PORT}")
            print(f"Directory: {DIRECTORY}")
            print("\nMake sure the Murder Agent API is running on port 5001")
            print("To start the API: python murder_agent_api.py")
            print("\nPress Ctrl+C to stop the server")

            # Try to open browser automatically
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print(f"\nOpened browser automatically")
            except:
                print(f"\nPlease open your browser and go to: http://localhost:{PORT}")

            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Error: Port {PORT} is already in use")
            print("Please stop any other servers running on this port or change the PORT variable")
        else:
            print(f"Error starting server: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    start_server()
