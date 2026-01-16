#!/usr/bin/env python3
"""
Simple script to start the JAI server
"""
import subprocess
import sys
import os

def main():
    print("🚀 Starting JAI Server...")
    print("This will start the backend server that voice_client.py connects to")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Change to the JAI directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Start the server
        subprocess.run([sys.executable, "jai_assistant.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
