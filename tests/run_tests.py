#!/usr/bin/env python3
"""
Run Tests Script
===============
Script to run all tests with proper configuration.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --backend          # Run only backend tests
    python run_tests.py --frontend         # Run only frontend tests
    python run_tests.py --api              # Run only API tests
    python run_tests.py --quick            # Skip slow tests
    python run_tests.py --cov              # Run with coverage report
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and capture output."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent.parent,  # Run from project root
        capture_output=False,
        text=True
    )
    
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Run GachaStats tests')
    parser.add_argument('--backend', action='store_true', help='Run only backend tests')
    parser.add_argument('--frontend', action='store_true', help='Run only frontend tests')
    parser.add_argument('--api', action='store_true', help='Run only API tests')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--e2e', action='store_true', help='Run only e2e tests')
    parser.add_argument('--quick', action='store_true', help='Skip slow tests')
    parser.add_argument('--cov', action='store_true', help='Run with coverage')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--fail-first', '-x', action='store_true', help='Stop on first failure')
    parser.add_argument('--markers', '-m', type=str, help='Run tests matching marker')
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = [sys.executable, '-m', 'pytest', 'tests/']
    
    # Add verbosity
    if args.verbose:
        cmd.append('-v')
    else:
        cmd.append('-v')  # Always verbose for now
    
    # Add fail fast
    if args.fail_first:
        cmd.append('-x')
    
    # Test selection
    test_paths = []
    
    if args.backend:
        test_paths.append('tests/backend/')
    elif args.frontend:
        test_paths.append('tests/frontend/')
    elif args.api:
        test_paths.append('tests/backend/api/')
    elif args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.e2e:
        cmd.extend(['-m', 'e2e'])
    elif args.markers:
        cmd.extend(['-m', args.markers])
    
    # Replace default path if specific paths selected
    if test_paths:
        cmd = [c for c in cmd if c != 'tests/']
        cmd.extend(test_paths)
    
    # Skip slow tests
    if args.quick:
        cmd.extend(['-m', 'not slow'])
    
    # Coverage
    if args.cov:
        cmd.insert(2, '--cov=backend')
        cmd.insert(3, '--cov-report=term-missing')
        cmd.insert(4, '--cov-report=html:htmlcov')
    
    # Run tests
    print("\n" + "="*60)
    print("GachaStats Test Suite")
    print("="*60)
    
    # Check if pytest is available
    check = subprocess.run(
        [sys.executable, '-c', 'import pytest'],
        capture_output=True
    )
    if check.returncode != 0:
        print("\nError: pytest not installed.")
        print("Install with: pip install pytest pytest-asyncio httpx")
        return 1
    
    # Run the tests
    returncode = run_command(cmd, "Test Suite")
    
    print("\n" + "="*60)
    if returncode == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests failed with exit code {returncode}")
    print("="*60)
    
    return returncode


if __name__ == '__main__':
    sys.exit(main())
