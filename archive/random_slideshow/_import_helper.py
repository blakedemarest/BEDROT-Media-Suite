"""
Import helper to ensure imports work correctly regardless of how the module is run.

This module handles the case where random_slideshow is run:
1. As a module from the project root (python -m src.random_slideshow.main)
2. Directly from within the directory (python main.py from src/random_slideshow/)
3. Via the launcher which changes to the module directory
"""

import sys
import os

def setup_imports():
    """Setup import paths to ensure the module can be imported correctly."""
    # Get the directory containing this file (src/random_slideshow)
    module_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get the src directory
    src_dir = os.path.dirname(module_dir)
    
    # Get the project root directory  
    project_root = os.path.dirname(src_dir)
    
    # Debug output
    debug = os.environ.get('DEBUG_IMPORTS', '').lower() == 'true'
    if debug:
        print(f"Import helper: module_dir = {module_dir}")
        print(f"Import helper: src_dir = {src_dir}")
        print(f"Import helper: project_root = {project_root}")
        print(f"Import helper: sys.path before = {sys.path[:3]}...")
    
    # Add project root to path if not already there
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Also add src directory for relative imports within src
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        
    # Add module directory for local imports
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    
    if debug:
        print(f"Import helper: sys.path after = {sys.path[:3]}...")
    
    return project_root, src_dir, module_dir

# Automatically setup imports when this module is imported
PROJECT_ROOT, SRC_DIR, MODULE_DIR = setup_imports()