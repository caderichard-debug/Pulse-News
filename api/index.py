import sys
import os

# Add the parent directory (which contains 'app') to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
