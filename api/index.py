import sys
from pathlib import Path

# Add parent directory to path so we can import from root
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from mangum import Mangum

# Vercel serverless handler using Mangum adapter
# Mangum converts ASGI (FastAPI) to AWS Lambda/Vercel format
handler = Mangum(app, lifespan="off")
