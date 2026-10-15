import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import app

# Vercel serverless handler
from mangum import Mangum
handler = Mangum(app)
