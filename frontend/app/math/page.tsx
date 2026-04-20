'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Textarea } from '@/components/ui/textarea'
import { Calculator, Function, Sigma, Matrix, BarChart3 } from 'lucide-react'
import 'katex/dist/katex.min.css'
import { InlineMath, BlockMath } from 'react-katex'

interface MathResult {
  type: string
  original?: string
  simplified?: string
  expanded?: string
  factored?: string
  solutions?: any[]
  latex?: string
  evaluated?: number
  error?: string
}

export default function MathPage() {
  const [expression, setExpression] = useState('')
  const [equation, setEquation] = useState('')
  const [variable, setVariable] = useState('x')
  const [matrix, setMatrix] = useState('[[1,2],[3,4]]')
  const [data, setData] = useState('1,2,3,4,5')
  const [result, setResult] = useState<MathResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleMathOperation = async (operation: string, params: any = {}) => {
    setLoading(true)
    setResult(null)
    
    try {
      const response = await fetch(`/api/math/${operation}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      })
      
      const data = await response.json()
      setResult(data)
    } catch (error) {
      setResult({ error: 'Failed to compute. Please check your input.' })
    } finally {
      setLoading(false)
    }
  }

  const renderLatex = (latex: string) => {
    try {
      return <InlineMath math={latex} errorColor="#cc0000" />
    } catch (error) {
      return <code className="bg-gray-100 px-2 py-1 rounded text-sm">{latex}</code>
    }
  }

  const renderResult = () => {
    if (!result) return null
    
    if (result.error) {
      return (
        <Alert variant="destructive">
          <AlertDescription>{result.error}</AlertDescription>
        </Alert>
      )
    }

    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5" />
            Result
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {result.original && (
            <div>
              <Label className="text-sm font-medium">Original</Label>
              <p className="font-mono text-sm">{result.original}</p>
            </div>
          )}
          
          {result.simplified && (
            <div>
              <Label className="text-sm font-medium">Simplified</Label>
              <p className="font-mono text-sm">{result.simplified}</p>
              {result.latex && (
                <div className="mt-1">
                  <Label className="text-xs text-gray-500">LaTeX</Label>
                  {renderLatex(result.latex)}
                </div>
              )}
            </div>
          )}
          
          {result.expanded && (
            <div>
              <Label className="text-sm font-medium">Expanded</Label>
              <p className="font-mono text-sm">{result.expanded}</p>
              {result.latex && renderLatex(result.latex)}
            </div>
          )}
          
          {result.factored && (
            <div>
              <Label className="text-sm font-medium">Factored</Label>
              <p className="font-mono text-sm">{result.factored}</p>
              {result.latex && renderLatex(result.latex)}
            </div>
          )}
          
          {result.solutions && (
            <div>
              <Label className="text-sm font-medium">Solutions</Label>
              <div className="flex flex-wrap gap-2">
                {result.solutions.map((sol, idx) => (
                  <Badge key={idx} variant="secondary">
                    {typeof sol === 'number' ? sol.toFixed(6) : sol}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          
          {result.evaluated !== undefined && (
            <div>
              <Label className="text-sm font-medium">Numerical Value</Label>
              <p className="font-mono text-sm">{result.evaluated.toFixed(6)}</p>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">JAI Mathematical Engine</h1>
        <p className="text-gray-600">
          Powered by SymPy and NumPy for symbolic and numerical computation
        </p>
      </div>

      <Tabs defaultValue="algebra" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="algebra" className="flex items-center gap-2">
            <Function className="h-4 w-4" />
            Algebra
          </TabsTrigger>
          <TabsTrigger value="calculus" className="flex items-center gap-2">
            <Sigma className="h-4 w-4" />
            Calculus
          </TabsTrigger>
          <TabsTrigger value="matrix" className="flex items-center gap-2">
            <Matrix className="h-4 w-4" />
            Matrix
          </TabsTrigger>
          <TabsTrigger value="statistics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Statistics
          </TabsTrigger>
          <TabsTrigger value="numerical" className="flex items-center gap-2">
            <Calculator className="h-4 w-4" />
            Numerical
          </TabsTrigger>
        </TabsList>

        <TabsContent value="algebra" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Algebraic Operations</CardTitle>
              <CardDescription>
                Simplify, expand, factor, and solve algebraic expressions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="expression">Expression</Label>
                <Input
                  id="expression"
                  placeholder="e.g., x^2 + 2*x + 1"
                  value={expression}
                  onChange={(e) => setExpression(e.target.value)}
                />
              </div>
              
              <div className="flex flex-wrap gap-2">
                <Button 
                  onClick={() => handleMathOperation('simplify', { expression })}
                  disabled={loading || !expression}
                >
                  Simplify
                </Button>
                <Button 
                  onClick={() => handleMathOperation('expand', { expression })}
                  disabled={loading || !expression}
                >
                  Expand
                </Button>
                <Button 
                  onClick={() => handleMathOperation('factor', { expression })}
                  disabled={loading || !expression}
                >
                  Factor
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Equation Solver</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="equation">Equation</Label>
                <Input
                  id="equation"
                  placeholder="e.g., x^2 - 4 = 0"
                  value={equation}
                  onChange={(e) => setEquation(e.target.value)}
                />
              </div>
              
              <div>
                <Label htmlFor="variable">Variable</Label>
                <Input
                  id="variable"
                  value={variable}
                  onChange={(e) => setVariable(e.target.value)}
                />
              </div>
              
              <Button 
                onClick={() => handleMathOperation('solve', { equation, variable })}
                disabled={loading || !equation}
              >
                Solve
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="calculus" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Calculus Operations</CardTitle>
              <CardDescription>
                Derivatives, integrals, and limits
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="calc-expression">Expression</Label>
                <Input
                  id="calc-expression"
                  placeholder="e.g., x^3 + 2*x^2 + x + 1"
                  value={expression}
                  onChange={(e) => setExpression(e.target.value)}
                />
              </div>
              
              <div>
                <Label htmlFor="calc-variable">Variable</Label>
                <Input
                  id="calc-variable"
                  value={variable}
                  onChange={(e) => setVariable(e.target.value)}
                />
              </div>
              
              <div className="flex flex-wrap gap-2">
                <Button 
                  onClick={() => handleMathOperation('derivative', { expression, variable })}
                  disabled={loading || !expression}
                >
                  Derivative
                </Button>
                <Button 
                  onClick={() => handleMathOperation('integral', { expression, variable })}
                  disabled={loading || !expression}
                >
                  Integral
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="matrix" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Matrix Operations</CardTitle>
              <CardDescription>
                Determinant, inverse, eigenvalues, and transpose
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="matrix">Matrix (JSON format)</Label>
                <Input
                  id="matrix"
                  placeholder="[[1,2],[3,4]]"
                  value={matrix}
                  onChange={(e) => setMatrix(e.target.value)}
                />
              </div>
              
              <div className="flex flex-wrap gap-2">
                <Button 
                  onClick={() => handleMathOperation('matrix', { matrix, operation: 'determinant' })}
                  disabled={loading || !matrix}
                >
                  Determinant
                </Button>
                <Button 
                  onClick={() => handleMathOperation('matrix', { matrix, operation: 'inverse' })}
                  disabled={loading || !matrix}
                >
                  Inverse
                </Button>
                <Button 
                  onClick={() => handleMathOperation('matrix', { matrix, operation: 'transpose' })}
                  disabled={loading || !matrix}
                >
                  Transpose
                </Button>
                <Button 
                  onClick={() => handleMathOperation('matrix', { matrix, operation: 'eigenvalues' })}
                  disabled={loading || !matrix}
                >
                  Eigenvalues
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="statistics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Statistical Analysis</CardTitle>
              <CardDescription>
                Basic statistics for numerical data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="data">Data (comma-separated)</Label>
                <Input
                  id="data"
                  placeholder="1,2,3,4,5"
                  value={data}
                  onChange={(e) => setData(e.target.value)}
                />
              </div>
              
              <Button 
                onClick={() => handleMathOperation('statistics', { 
                  data: data.split(',').map(d => parseFloat(d.trim())).filter(d => !isNaN(d)) 
                })}
                disabled={loading || !data}
              >
                Calculate Statistics
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="numerical" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Numerical Methods</CardTitle>
              <CardDescription>
                Numerical root finding
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="num-expression">Expression</Label>
                <Input
                  id="num-expression"
                  placeholder="e.g., x^3 - 2*x - 5"
                  value={expression}
                  onChange={(e) => setExpression(e.target.value)}
                />
              </div>
              
              <div>
                <Label htmlFor="initial-guess">Initial Guess</Label>
                <Input
                  id="initial-guess"
                  type="number"
                  value="0"
                  onChange={(e) => setVariable(e.target.value)}
                />
              </div>
              
              <Button 
                onClick={() => handleMathOperation('numerical', { 
                  expression, 
                  variable: 'x', 
                  initial_guess: 0 
                })}
                disabled={loading || !expression}
              >
                Find Root
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {renderResult()}
    </div>
  )
}
