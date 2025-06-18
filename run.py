#!/usr/bin/env python3
"""
Frontend server startup script for the Murder Agent UI
"""

import os
import http.server
import socketserver
import webbrowser
import sys
from pathlib import Path

# Configuration
PORT = 8080
DIRECTORY = Path(__file__).parent / "src"

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
    """Start the frontend web server"""
    try:
        print("=" * 60)
        print("🌐 Murder Agent Frontend Server")
        print("=" * 60)
        
        # Check if src directory exists
        if not DIRECTORY.exists():
            print(f"✗ Source directory not found: {DIRECTORY}")
            print("Please ensure the frontend files are in the 'src' directory")
            return False
        
        # Check if required files exist
        required_files = ['index.html', 'login.html', 'styles.css', 'script.js']
        missing_files = []
        for file in required_files:
            if not (DIRECTORY / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"✗ Missing required files: {', '.join(missing_files)}")
            return False
        
        print("✓ All frontend files found")
        
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"\n🚀 Frontend server starting...")
            print(f"🌐 Web Interface: http://localhost:{PORT}")
            print(f"📁 Serving from: {DIRECTORY}")
            print("\nMake sure the Murder Agent API is running on port 5001")
            print("To start the API: cd ../backend && python run.py")
            print("\nPress Ctrl+C to stop the server")
            print("=" * 60)

            # Try to open browser automatically
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print(f"\n✓ Opened browser automatically")
            except:
                print(f"\nPlease open your browser and go to: http://localhost:{PORT}")

            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n✓ Frontend server stopped by user")
        return True
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"✗ Port {PORT} is already in use")
            print("Please stop any other servers running on this port or change the PORT variable")
        else:
            print(f"✗ Error starting server: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    try:
        success = start_server()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
