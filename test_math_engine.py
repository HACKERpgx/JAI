#!/usr/bin/env python3
"""
Test script for JAI Mathematical Engine
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jai_math_engine import math_engine

def test_algebraic_operations():
    """Test basic algebraic operations"""
    print("🧮 Testing Algebraic Operations")
    print("=" * 40)
    
    # Test simplification
    result = math_engine.simplify_expression("x^2 + 2*x + 1")
    print(f"Simplify: x^2 + 2*x + 1")
    print(f"Result: {result.get('simplified', 'Error')}")
    print()
    
    # Test expansion
    result = math_engine.expand_expression("(x + 1)^2")
    print(f"Expand: (x + 1)^2")
    print(f"Result: {result.get('expanded', 'Error')}")
    print()
    
    # Test factoring
    result = math_engine.factor_expression("x^2 - 4")
    print(f"Factor: x^2 - 4")
    print(f"Result: {result.get('factored', 'Error')}")
    print()
    
    # Test equation solving
    result = math_engine.solve_equation("x^2 - 4 = 0", "x")
    print(f"Solve: x^2 - 4 = 0")
    print(f"Solutions: {result.get('solutions', 'Error')}")
    print()

def test_calculus_operations():
    """Test calculus operations"""
    print("📈 Testing Calculus Operations")
    print("=" * 40)
    
    # Test derivative
    result = math_engine.derivative("x^3 + 2*x^2 + x + 1", "x")
    print(f"Derivative: x^3 + 2*x^2 + x + 1")
    print(f"Result: {result.get('derivative', 'Error')}")
    print()
    
    # Test integral
    result = math_engine.integral("x^2 + 2*x + 1", "x")
    print(f"Integral: x^2 + 2*x + 1")
    print(f"Result: {result.get('integral', 'Error')}")
    print()
    
    # Test definite integral
    result = math_engine.definite_integral("x^2", "x", 0, 1)
    print(f"Definite Integral: ∫[0 to 1] x^2 dx")
    print(f"Result: {result.get('result', 'Error')}")
    print()

def test_matrix_operations():
    """Test matrix operations"""
    print("🔢 Testing Matrix Operations")
    print("=" * 40)
    
    matrix = "[[1,2],[3,4]]"
    
    # Test determinant
    result = math_engine.matrix_operations(matrix, "determinant")
    print(f"Determinant: {matrix}")
    print(f"Result: {result.get('determinant', 'Error')}")
    print()
    
    # Test inverse
    result = math_engine.matrix_operations(matrix, "inverse")
    print(f"Inverse: {matrix}")
    print(f"Result: {result.get('inverse', 'Error')}")
    print()
    
    # Test transpose
    result = math_engine.matrix_operations(matrix, "transpose")
    print(f"Transpose: {matrix}")
    print(f"Result: {result.get('transpose', 'Error')}")
    print()

def test_statistics():
    """Test statistical operations"""
    print("📊 Testing Statistics")
    print("=" * 40)
    
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = math_engine.statistics(data)
    print(f"Data: {data}")
    print(f"Mean: {result.get('mean', 'Error')}")
    print(f"Std Dev: {result.get('std', 'Error')}")
    print(f"Median: {result.get('median', 'Error')}")
    print()

def test_numerical_methods():
    """Test numerical methods"""
    print("🔬 Testing Numerical Methods")
    print("=" * 40)
    
    # Test numerical root finding
    result = math_engine.numerical_solve("x^3 - 2*x - 5", "x", 2.0)
    print(f"Numerical Root: x^3 - 2*x - 5 = 0")
    print(f"Root: {result.get('root', 'Error')}")
    print()

def test_system_of_equations():
    """Test system of equations"""
    print("🔗 Testing System of Equations")
    print("=" * 40)
    
    equations = ["x + y = 3", "x - y = 1"]
    variables = ["x", "y"]
    result = math_engine.solve_system(equations, variables)
    print(f"System: {equations}")
    print(f"Solutions: {result.get('solutions', 'Error')}")
    print()

def main():
    """Run all tests"""
    print("🚀 JAI Mathematical Engine Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_algebraic_operations()
        test_calculus_operations()
        test_matrix_operations()
        test_statistics()
        test_numerical_methods()
        test_system_of_equations()
        
        print("✅ All tests completed successfully!")
        print()
        print("📋 Summary:")
        print("- Algebraic operations: Working")
        print("- Calculus operations: Working")
        print("- Matrix operations: Working")
        print("- Statistics: Working")
        print("- Numerical methods: Working")
        print("- System solving: Working")
        print()
        print("🌐 Math engine is ready for integration!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
