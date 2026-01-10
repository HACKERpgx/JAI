#!/usr/bin/env python3
"""
Test JAI's intelligence upgrade with various questions.
"""
import sys
import requests
from requests.auth import HTTPBasicAuth

# Configuration
SERVER_URL = "http://localhost:8001"
USERNAME = "admin"
PASSWORD = "adminpass"

def test_question(question: str) -> str:
    """Send a question to JAI and get response."""
    try:
        response = requests.post(
            f"{SERVER_URL}/command",
            json={"command": question},
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=45
        )
        response.raise_for_status()
        data = response.json()
        return data.get('response', 'No response')
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    """Test JAI's intelligence with various questions."""
    print("=" * 70)
    print("JAI INTELLIGENCE TEST")
    print("=" * 70)
    print("\nMake sure JAI server is running on http://localhost:8001")
    print("\nTesting upgraded AI model (Gemini 2.0)...\n")
    
    test_questions = [
        # General Knowledge
        ("What is quantum physics?", "Science"),
        ("Who invented the telephone?", "History"),
        ("What is the largest planet?", "Astronomy"),
        
        # Mathematics
        ("What is 15 times 23?", "Math"),
        ("What is 20 percent of 150?", "Math"),
        
        # Technology
        ("What is artificial intelligence?", "Technology"),
        ("How does GPS work?", "Technology"),
        
        # Practical
        ("What is the capital of Pakistan?", "Geography"),
        ("How many days in a year?", "General"),
    ]
    
    for i, (question, category) in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_questions)} - {category}")
        print(f"{'='*70}")
        print(f"Q: {question}")
        print(f"\nA: ", end="", flush=True)
        
        answer = test_question(question)
        print(answer)
        
        if i < len(test_questions):
            input("\nPress Enter for next question...")
    
    print("\n" + "="*70)
    print("TESTING COMPLETE!")
    print("="*70)
    print("\n✅ If you got detailed, intelligent answers, the upgrade worked!")
    print("❌ If you got errors or simple answers, check the server logs.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
