#!/usr/bin/env python3
"""
Startup script for the Murder Agent system
Starts both the API server and web UI server
"""

import subprocess
import sys
import time
import webbrowser
import threading
import signal
import os
from pathlib import Path

# Configuration
API_PORT = 5001
WEB_PORT = 8080
API_SCRIPT = "murder_agent_api.py"
WEB_SCRIPT = "web_server.py"

class MurderAgentLauncher:
    def __init__(self):
        self.api_process = None
        self.web_process = None
        self.running = True
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        try:
            import flask
            import flask_cors
            import requests
            print("✓ All dependencies are installed")
            return True
        except ImportError as e:
            print(f"✗ Missing dependency: {e}")
            print("Please install dependencies: pip install -r requirements.txt")
            return False
    
    def start_api_server(self):
        """Start the Murder Agent API server"""
        try:
            print(f"Starting Murder Agent API on port {API_PORT}...")
            self.api_process = subprocess.Popen([
                sys.executable, API_SCRIPT
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give the API server time to start
            time.sleep(3)
            
            if self.api_process.poll() is None:
                print(f"✓ Murder Agent API started successfully")
                return True
            else:
                stdout, stderr = self.api_process.communicate()
                print(f"✗ API server failed to start")
                print(f"Error: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"✗ Error starting API server: {e}")
            return False
    
    def start_web_server(self):
        """Start the web UI server"""
        try:
            print(f"Starting Web UI server on port {WEB_PORT}...")
            self.web_process = subprocess.Popen([
                sys.executable, WEB_SCRIPT
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give the web server time to start
            time.sleep(2)
            
            if self.web_process.poll() is None:
                print(f"✓ Web UI server started successfully")
                return True
            else:
                stdout, stderr = self.web_process.communicate()
                print(f"✗ Web server failed to start")
                print(f"Error: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"✗ Error starting web server: {e}")
            return False
    
    def open_browser(self):
        """Open the web interface in browser"""
        try:
            time.sleep(1)  # Wait a moment for servers to be ready
            webbrowser.open(f'http://localhost:{WEB_PORT}')
            print(f"✓ Opened browser at http://localhost:{WEB_PORT}")
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print(f"Please manually open: http://localhost:{WEB_PORT}")
    
    def monitor_processes(self):
        """Monitor the running processes"""
        while self.running:
            try:
                # Check API process
                if self.api_process and self.api_process.poll() is not None:
                    print("⚠ API server stopped unexpectedly")
                    break
                
                # Check Web process
                if self.web_process and self.web_process.poll() is not None:
                    print("⚠ Web server stopped unexpectedly")
                    break
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                break
    
    def cleanup(self):
        """Clean up processes"""
        print("\nShutting down servers...")
        
        if self.api_process:
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=5)
                print("✓ API server stopped")
            except:
                self.api_process.kill()
                print("✓ API server force stopped")
        
        if self.web_process:
            try:
                self.web_process.terminate()
                self.web_process.wait(timeout=5)
                print("✓ Web server stopped")
            except:
                self.web_process.kill()
                print("✓ Web server force stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """Main run method"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("=" * 60)
        print("🔍 Murder Agent System Launcher")
        print("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Check if files exist
        if not Path(API_SCRIPT).exists():
            print(f"✗ API script not found: {API_SCRIPT}")
            return False
        
        if not Path(WEB_SCRIPT).exists():
            print(f"✗ Web script not found: {WEB_SCRIPT}")
            return False
        
        # Start servers
        if not self.start_api_server():
            return False
        
        if not self.start_web_server():
            self.cleanup()
            return False
        
        # Open browser
        browser_thread = threading.Thread(target=self.open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        print("\n" + "=" * 60)
        print("🚀 Murder Agent System is running!")
        print("=" * 60)
        print(f"📡 API Server: http://localhost:{API_PORT}")
        print(f"🌐 Web Interface: http://localhost:{WEB_PORT}")
        print("\nPress Ctrl+C to stop all servers")
        print("=" * 60)
        
        # Monitor processes
        try:
            self.monitor_processes()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
        
        return True

def main():
    """Main function"""
    launcher = MurderAgentLauncher()
    
    try:
        success = launcher.run()
        if not success:
            print("\n❌ Failed to start Murder Agent system")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        launcher.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
