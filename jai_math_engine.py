#!/usr/bin/env python3
"""
JAI Mathematical Computation Engine
Provides symbolic and numerical mathematics capabilities using SymPy and NumPy
"""

import sympy as sp
import numpy as np
from typing import Dict, Any, List, Union, Optional
import json
import re

class JAIMathEngine:
    """Mathematical computation engine for JAI Assistant"""
    
    def __init__(self):
        self.symbols = {}  # Store user-defined symbols
        self.last_result = None
    
    def parse_expression(self, expr: str) -> sp.Expr:
        """Parse mathematical expression with user-defined symbols"""
        try:
            # Replace common mathematical notation
            expr = expr.replace('^', '**')
            expr = expr.replace('pi', 'sp.pi')
            expr = expr.replace('e', 'sp.E')
            
            # Add user-defined symbols to namespace
            namespace = {'sp': sp, 'np': np, **self.symbols}
            
            # Parse the expression
            parsed = sp.sympify(expr, locals=namespace)
            return parsed
        except Exception as e:
            raise ValueError(f"Failed to parse expression: {e}")
    
    def simplify_expression(self, expr: str) -> Dict[str, Any]:
        """Simplify algebraic expression"""
        try:
            parsed = self.parse_expression(expr)
            simplified = sp.simplify(parsed)
            
            return {
                'type': 'simplification',
                'original': str(parsed),
                'simplified': str(simplified),
                'latex': sp.latex(simplified),
                'evaluated': float(simplified.evalf()) if simplified.is_number else None
            }
        except Exception as e:
            return {'error': str(e)}
    
    def expand_expression(self, expr: str) -> Dict[str, Any]:
        """Expand algebraic expression"""
        try:
            parsed = self.parse_expression(expr)
            expanded = sp.expand(parsed)
            
            return {
                'type': 'expansion',
                'original': str(parsed),
                'expanded': str(expanded),
                'latex': sp.latex(expanded)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def factor_expression(self, expr: str) -> Dict[str, Any]:
        """Factor algebraic expression"""
        try:
            parsed = self.parse_expression(expr)
            factored = sp.factor(parsed)
            
            return {
                'type': 'factorization',
                'original': str(parsed),
                'factored': str(factored),
                'latex': sp.latex(factored)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def solve_equation(self, equation: str, variable: str = 'x') -> Dict[str, Any]:
        """Solve equation for specified variable"""
        try:
            # Parse equation (handle both = and ==)
            if '=' in equation:
                left, right = equation.split('=', 1)
                left_expr = self.parse_expression(left.strip())
                right_expr = self.parse_expression(right.strip())
                eq = sp.Eq(left_expr, right_expr)
            else:
                expr = self.parse_expression(equation)
                eq = sp.Eq(expr, 0)
            
            var = sp.Symbol(variable)
            solutions = sp.solve(eq, var)
            
            # Convert solutions to readable format
            solution_list = []
            for sol in solutions:
                if sol.is_real:
                    solution_list.append(float(sol.evalf()))
                else:
                    solution_list.append(str(sol))
            
            return {
                'type': 'equation_solving',
                'equation': str(eq),
                'variable': variable,
                'solutions': solution_list,
                'latex_solutions': [sp.latex(sol) for sol in solutions]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def solve_system(self, equations: List[str], variables: List[str]) -> Dict[str, Any]:
        """Solve system of equations"""
        try:
            eqs = []
            for eq_str in equations:
                if '=' in eq_str:
                    left, right = eq_str.split('=', 1)
                    left_expr = self.parse_expression(left.strip())
                    right_expr = self.parse_expression(right.strip())
                    eqs.append(sp.Eq(left_expr, right_expr))
                else:
                    expr = self.parse_expression(eq_str)
                    eqs.append(sp.Eq(expr, 0))
            
            vars_syms = [sp.Symbol(var) for var in variables]
            solutions = sp.solve(eqs, vars_syms, dict=True)
            
            if not solutions:
                return {'error': 'No solutions found'}
            
            # Convert first solution to readable format
            solution_dict = solutions[0]
            formatted_solutions = {}
            for var, sol in solution_dict.items():
                if sol.is_real:
                    formatted_solutions[str(var)] = float(sol.evalf())
                else:
                    formatted_solutions[str(var)] = str(sol)
            
            return {
                'type': 'system_solving',
                'equations': equations,
                'variables': variables,
                'solutions': formatted_solutions,
                'latex': sp.latex(solution_dict)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def derivative(self, expr: str, variable: str = 'x', order: int = 1) -> Dict[str, Any]:
        """Calculate derivative of expression"""
        try:
            parsed = self.parse_expression(expr)
            var = sp.Symbol(variable)
            
            if order == 1:
                result = sp.diff(parsed, var)
            else:
                result = sp.diff(parsed, var, order)
            
            return {
                'type': 'derivative',
                'expression': str(parsed),
                'variable': variable,
                'order': order,
                'derivative': str(result),
                'latex': sp.latex(result)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def integral(self, expr: str, variable: str = 'x') -> Dict[str, Any]:
        """Calculate indefinite integral of expression"""
        try:
            parsed = self.parse_expression(expr)
            var = sp.Symbol(variable)
            result = sp.integrate(parsed, var)
            
            return {
                'type': 'integral',
                'expression': str(parsed),
                'variable': variable,
                'integral': str(result) + ' + C',
                'latex': sp.latex(result) + ' + C'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def definite_integral(self, expr: str, variable: str, lower: Union[str, float], upper: Union[str, float]) -> Dict[str, Any]:
        """Calculate definite integral"""
        try:
            parsed = self.parse_expression(expr)
            var = sp.Symbol(variable)
            
            # Parse limits
            if isinstance(lower, str):
                lower_val = self.parse_expression(lower)
            else:
                lower_val = lower
            
            if isinstance(upper, str):
                upper_val = self.parse_expression(upper)
            else:
                upper_val = upper
            
            result = sp.integrate(parsed, (var, lower_val, upper_val))
            
            return {
                'type': 'definite_integral',
                'expression': str(parsed),
                'variable': variable,
                'lower': str(lower_val),
                'upper': str(upper_val),
                'result': str(result),
                'evaluated': float(result.evalf()) if result.is_number else None,
                'latex': sp.latex(result)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def limit(self, expr: str, variable: str, point: Union[str, float], direction: str = '+') -> Dict[str, Any]:
        """Calculate limit of expression"""
        try:
            parsed = self.parse_expression(expr)
            var = sp.Symbol(variable)
            
            if isinstance(point, str):
                point_val = self.parse_expression(point)
            else:
                point_val = point
            
            if direction == '+':
                result = sp.limit(parsed, var, point_val, dir='+')
            elif direction == '-':
                result = sp.limit(parsed, var, point_val, dir='-')
            else:
                result = sp.limit(parsed, var, point_val)
            
            return {
                'type': 'limit',
                'expression': str(parsed),
                'variable': variable,
                'point': str(point_val),
                'direction': direction,
                'limit': str(result),
                'latex': sp.latex(result)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def matrix_operations(self, matrix_str: str, operation: str) -> Dict[str, Any]:
        """Perform matrix operations using NumPy"""
        try:
            # Parse matrix string (format: [[1,2],[3,4]])
            matrix = np.array(json.loads(matrix_str))
            
            if operation == 'determinant':
                if matrix.shape[0] != matrix.shape[1]:
                    return {'error': 'Matrix must be square for determinant'}
                result = np.linalg.det(matrix)
                return {
                    'type': 'matrix_determinant',
                    'matrix': matrix.tolist(),
                    'determinant': float(result),
                    'latex': f'\\det\\begin{{pmatrix}}{self._matrix_to_latex(matrix)}\\end{{pmatrix}}'
                }
            
            elif operation == 'inverse':
                if matrix.shape[0] != matrix.shape[1]:
                    return {'error': 'Matrix must be square for inverse'}
                result = np.linalg.inv(matrix)
                return {
                    'type': 'matrix_inverse',
                    'matrix': matrix.tolist(),
                    'inverse': result.tolist(),
                    'latex': f'\\begin{{pmatrix}}{self._matrix_to_latex(result)}\\end{{pmatrix}}'
                }
            
            elif operation == 'eigenvalues':
                if matrix.shape[0] != matrix.shape[1]:
                    return {'error': 'Matrix must be square for eigenvalues'}
                eigenvals, eigenvecs = np.linalg.eig(matrix)
                return {
                    'type': 'matrix_eigenvalues',
                    'matrix': matrix.tolist(),
                    'eigenvalues': [complex(val) for val in eigenvals],
                    'eigenvectors': eigenvecs.tolist()
                }
            
            elif operation == 'transpose':
                result = matrix.T
                return {
                    'type': 'matrix_transpose',
                    'matrix': matrix.tolist(),
                    'transpose': result.tolist(),
                    'latex': f'\\begin{{pmatrix}}{self._matrix_to_latex(result)}\\end{{pmatrix}}'
                }
            
            else:
                return {'error': f'Unknown operation: {operation}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _matrix_to_latex(self, matrix: np.ndarray) -> str:
        """Convert matrix to LaTeX format"""
        rows = []
        for row in matrix:
            row_str = ' & '.join([f'{val:.6g}' if isinstance(val, (int, float)) else str(val) for val in row])
            rows.append(row_str)
        return '\\\\'.join(rows)
    
    def numerical_solve(self, expr: str, variable: str = 'x', initial_guess: float = 0.0) -> Dict[str, Any]:
        """Numerical root finding using NumPy"""
        try:
            parsed = self.parse_expression(expr)
            var = sp.Symbol(variable)
            
            # Convert to lambda function for numerical evaluation
            f = sp.lambdify(var, parsed, 'numpy')
            
            # Use numerical root finding
            from scipy.optimize import fsolve
            root = fsolve(f, initial_guess)[0]
            
            return {
                'type': 'numerical_root',
                'expression': str(parsed),
                'variable': variable,
                'root': float(root),
                'initial_guess': initial_guess
            }
        except ImportError:
            # Fallback to simple Newton's method if scipy not available
            try:
                parsed = self.parse_expression(expr)
                var = sp.Symbol(variable)
                f = sp.lambdify(var, parsed, 'numpy')
                df = sp.lambdify(var, sp.diff(parsed, var), 'numpy')
                
                x = initial_guess
                for _ in range(100):  # Max iterations
                    fx = f(x)
                    dfx = df(x)
                    if abs(dfx) < 1e-10:
                        break
                    x_new = x - fx/dfx
                    if abs(x_new - x) < 1e-10:
                        break
                    x = x_new
                
                return {
                    'type': 'numerical_root',
                    'expression': str(parsed),
                    'variable': variable,
                    'root': float(x),
                    'initial_guess': initial_guess,
                    'method': 'newton'
                }
            except Exception as e:
                return {'error': str(e)}
        except Exception as e:
            return {'error': str(e)}
    
    def statistics(self, data: List[float]) -> Dict[str, Any]:
        """Calculate basic statistics using NumPy"""
        try:
            arr = np.array(data)
            
            return {
                'type': 'statistics',
                'count': len(data),
                'mean': float(np.mean(arr)),
                'median': float(np.median(arr)),
                'std': float(np.std(arr)),
                'var': float(np.var(arr)),
                'min': float(np.min(arr)),
                'max': float(np.max(arr)),
                'percentiles': {
                    '25': float(np.percentile(arr, 25)),
                    '50': float(np.percentile(arr, 50)),
                    '75': float(np.percentile(arr, 75))
                }
            }
        except Exception as e:
            return {'error': str(e)}

# Global instance
math_engine = JAIMathEngine()
