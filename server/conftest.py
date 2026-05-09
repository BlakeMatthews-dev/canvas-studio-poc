import sys
from pathlib import Path

# Make server/ the Python root so `from engine.xxx import yyy` works in tests
sys.path.insert(0, str(Path(__file__).parent))
