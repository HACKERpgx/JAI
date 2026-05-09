
import unittest
import sys
import os

# Add the current directory to sys.path to import jai_assistant
sys.path.append(os.getcwd())

from jai_assistant import is_mathematical_query

class TestMathQueryRefinement(unittest.TestCase):
    def test_false_positives(self):
        # These should NOT be detected as math queries now
        self.assertFalse(is_mathematical_query("what emotion are they probably expressing and why?"))
        self.assertFalse(is_mathematical_query("Tell me about statistics in France"))
        self.assertFalse(is_mathematical_query("What is the meaning of this expression?"))
        self.assertFalse(is_mathematical_query("Solve the mystery of the missing cat"))
        self.assertFalse(is_mathematical_query("Calculate the risks of starting a business"))

    def test_true_positives(self):
        # These SHOULD still be detected as math queries
        self.assertTrue(is_mathematical_query("solve 2x + 5 = 10"))
        self.assertTrue(is_mathematical_query("calculate 500 * 1.2"))
        self.assertTrue(is_mathematical_query("simplify (x+2)^2"))
        self.assertTrue(is_mathematical_query("what is the sin(45)"))
        self.assertTrue(is_mathematical_query("integrate x^2 from 0 to 1"))
        self.assertTrue(is_mathematical_query("calculate the mean of 10, 20, 30"))

if __name__ == "__main__":
    unittest.main()
