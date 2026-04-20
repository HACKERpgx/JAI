#!/usr/bin/env python3
"""
Test script for JAI manual mathematical reasoning
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jai_assistant import solve_mathematical_problem_manual

def test_manual_math():
    """Test manual mathematical reasoning"""
    print("Testing JAI Manual Mathematical Reasoning")
    print("=" * 50)
    
    # Test cases that should work with manual reasoning
    test_cases = [
        "What is 2 + 2?",
        "Calculate 15 * 8", 
        "What is 3^4?",
        "Solve 2x + 5 = 15",
        "Solve x^2 - 4 = 0",
        "Simplify x^2 + 2*x + 1",
        "Factor x^2 - 9",
        "What is the derivative of x^3?",
        "Integrate x^2",
        "What is 10 / 2?"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        print("-" * 30)
        
        try:
            response = solve_mathematical_problem_manual(test_case)
            print(f"JAI Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Manual math reasoning testing completed!")

if __name__ == "__main__":
    test_manual_math()
