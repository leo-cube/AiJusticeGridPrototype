#!/usr/bin/env python3
"""
Convenience script to run the frontend server from the root directory
"""

import os
import sys
from pathlib import Path

def main():
    """Run the frontend server"""
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        print("Please ensure the frontend folder exists in the current directory.")
        return False
    
    # Change to frontend directory
    os.chdir(frontend_dir)
    
    # Import and run the frontend
    try:
        from run import main as run_frontend
        return run_frontend()
    except ImportError:
        print("❌ Frontend run script not found!")
        print("Please ensure frontend/run.py exists.")
        return False
    except Exception as e:
        print(f"❌ Error running frontend: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
