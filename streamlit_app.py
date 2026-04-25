# Streamlit Cloud entrypoint
# Imports Home.py content to run as the main entry point
import sys
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run Home.py
exec(open(Path(__file__).parent / "Home.py").read())

