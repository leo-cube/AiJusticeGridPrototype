#!/usr/bin/env python3
"""
Backend server startup script for the Murder Agent API
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import httpx
        import pydantic
        import requests
        import reportlab
        print("✓ All backend dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False

def main():
    """Main function to start the backend server"""
    print("=" * 60)
    print("🔍 Murder Agent Backend API Server")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\nInstalling dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✓ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("✗ Failed to install dependencies")
            return False
    
    # Check if app.py exists
    if not Path("app.py").exists():
        print("✗ app.py not found in current directory")
        return False
    
    print("\n🚀 Starting FastAPI server...")
    print("📡 API Server: http://localhost:5001")
    print("📚 API Documentation: http://localhost:5001/docs")
    print("📖 ReDoc Documentation: http://localhost:5001/redoc")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Start the FastAPI server using uvicorn
        import uvicorn
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=5001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n✓ Server stopped by user")
    except Exception as e:
        print(f"\n✗ Error starting server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
