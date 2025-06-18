#!/usr/bin/env python3
"""
Convenience script to run the backend server from the root directory
"""

import os
import sys
from pathlib import Path

def main():
    """Run the backend server"""
    backend_dir = Path(__file__).parent / "backend"
    
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        print("Please ensure the backend folder exists in the current directory.")
        return False
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Import and run the backend
    try:
        from run import main as run_backend
        return run_backend()
    except ImportError:
        print("❌ Backend run script not found!")
        print("Please ensure backend/run.py exists.")
        return False
    except Exception as e:
        print(f"❌ Error running backend: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
