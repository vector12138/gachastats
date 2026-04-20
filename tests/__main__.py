#!/usr/bin/env python3
"""Test suite entry point - enables: python -m tests"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run test suite."""
    # Change to project root
    project_root = Path(__file__).parent.parent
    
    # Run pytest
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
