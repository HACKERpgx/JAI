#!/usr/bin/env python3
"""
Test script for JAI mathematical problem solving in chat
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jai_assistant import execute_command, UserSession

def test_math_in_chat():
    """Test mathematical problem solving in regular chat"""
    print("Testing JAI Mathematical Problem Solving in Chat")
    print("=" * 50)
    
    # Create a test session
    session = UserSession("test_user")
    
    # Test cases
    test_cases = [
        "What is 2 + 2?",
        "Solve x^2 - 4 = 0",
        "Simplify x^2 + 2*x + 1",
        "Calculate 15 * 8",
        "What is the derivative of x^3?",
        "Integrate x^2",
        "Factor x^2 - 9",
        "Expand (x + 2)^2",
        "Solve 2*x + 5 = 15",
        "What is 3^4?"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        print("-" * 30)
        
        try:
            response = execute_command(test_case, session, suppress_tts=True)
            print(f"JAI Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Chat math testing completed!")

if __name__ == "__main__":
    test_math_in_chat()
