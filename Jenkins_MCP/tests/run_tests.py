"""Test runner script for Jenkins MCP Server."""

import sys
import subprocess
import os
from pathlib import Path


def run_tests():
    """Run the test suite."""
    project_root = Path(__file__).parent.parent
    
    print("=== Jenkins MCP Server Test Suite ===")
    print(f"Project root: {project_root}")
    
    # Check if pytest is available
    try:
        import pytest
        print("✓ pytest is available")
    except ImportError:
        print("✗ pytest not found. Installing test dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pytest", "pytest-cov", "pytest-asyncio"
        ], check=True)
        print("✓ Test dependencies installed")
    
    # Set environment variables for testing
    test_env = os.environ.copy()
    test_env.update({
        "JENKINS_URL": "http://localhost:8080",
        "JENKINS_USERNAME": "test_user",
        "JENKINS_TOKEN": "test_token",
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "true"
    })
    
    # Run tests with coverage
    test_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=jenkins_mcp_server",  # Coverage for our package
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html:htmlcov",  # HTML coverage report
        str(project_root / "tests")  # Tests directory
    ]
    
    print("\n=== Running Tests ===")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest"
        ] + test_args, env=test_env, cwd=project_root)
        
        if result.returncode == 0:
            print("\n✓ All tests passed!")
            print("Coverage report generated in htmlcov/index.html")
        else:
            print(f"\n✗ Tests failed with exit code: {result.returncode}")
            
        return result.returncode
        
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        return 1


def run_linting():
    """Run code linting."""
    project_root = Path(__file__).parent.parent
    
    print("\n=== Running Code Linting ===")
    
    # Install linting tools if needed
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "black", "isort", "flake8", "mypy"
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Warning: Could not install linting tools")
    
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    
    # Run black (code formatting)
    print("Running black...")
    try:
        subprocess.run([
            sys.executable, "-m", "black", "--check", str(src_dir), str(tests_dir)
        ], check=True)
        print("✓ Code formatting is correct")
    except subprocess.CalledProcessError:
        print("✗ Code formatting issues found. Run 'black src tests' to fix.")
    
    # Run isort (import sorting)
    print("Running isort...")
    try:
        subprocess.run([
            sys.executable, "-m", "isort", "--check-only", str(src_dir), str(tests_dir)
        ], check=True)
        print("✓ Import sorting is correct")
    except subprocess.CalledProcessError:
        print("✗ Import sorting issues found. Run 'isort src tests' to fix.")
    
    # Run flake8 (style checking)
    print("Running flake8...")
    try:
        subprocess.run([
            sys.executable, "-m", "flake8", str(src_dir), str(tests_dir)
        ], check=True)
        print("✓ No style issues found")
    except subprocess.CalledProcessError:
        print("✗ Style issues found")


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Jenkins MCP Server Test Runner")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--no-lint", action="store_true", help="Skip linting")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    exit_code = 0
    
    if args.lint:
        run_linting()
        return
    
    # Run tests
    test_result = run_tests()
    if test_result != 0:
        exit_code = test_result
    
    # Run linting unless explicitly disabled
    if not args.no_lint:
        run_linting()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())