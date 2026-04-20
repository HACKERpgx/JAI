#!/usr/bin/env python3
"""
Test script for JAI mathematical notation normalization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jai_assistant import normalize_math_notation, solve_mathematical_problem

def test_notation_normalization():
    """Test mathematical notation normalization"""
    print("Testing JAI Mathematical Notation Normalization")
    print("=" * 60)
    
    # Test notation normalization
    test_cases = [
        "What is log2 of 8?",
        "Calculate x2 + y2",
        "What is alpha/beta?",
        "Solve x2 = 16",
        "What is sqrt(25)?",
        "Calculate log10 of 100",
        "What is pi * r2?",
        "Solve for theta where sin(theta) = 0.5"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        print("-" * 40)
        
        # Show normalized version
        normalized = normalize_math_notation(test_case)
        print(f"Normalized: {normalized}")
        
        # Try to solve it
        try:
            response = solve_mathematical_problem(test_case)
            print(f"JAI Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Notation normalization testing completed!")

if __name__ == "__main__":
    test_notation_normalization()
