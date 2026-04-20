#!/usr/bin/env python3
"""
Test script for JAI multi-question mathematical problem solving
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jai_assistant import solve_mathematical_problem

def test_multi_question():
    """Test handling of multiple mathematical questions in one message"""
    print("Testing JAI Multi-Question Mathematical Problem Solving")
    print("=" * 60)
    
    # Test cases with multiple questions
    test_cases = [
        "1. What is 2 + 2? 2. What is 3 * 4? 3. What is 10 / 2?",
        "What is 5 + 5 and what is 10 - 3?",
        "Calculate 15 * 8 also calculate 12 / 4",
        "Simplify x^2 + 2*x + 1\nFactor x^2 - 9",
        "What is 3^4? Additionally, what is 2^3?",
        "What is 2 + 2? What is 3 * 3? What is 10 / 5?"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        print("-" * 40)
        
        try:
            response = solve_mathematical_problem(test_case)
            print(f"JAI Response:\n{response}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Multi-question math testing completed!")

if __name__ == "__main__":
    test_multi_question()
