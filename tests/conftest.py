import sys
import os

# Add project root to sys.path so that 'src' modules can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root) 