"""
Setup Verification Script

Run this script to verify your environment is correctly configured.
This checks all imports, dependencies, and basic functionality.
"""

import sys
import os
from typing import List, Tuple

def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(text)
    print("="*70)

def print_result(test_name: str, passed: bool, message: str = ""):
    """
    Print a test result.
    
    Note: This function prints messages to stdout. Do not pass sensitive
    information (API keys, passwords, etc.) in the message parameter.
    """
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status:8} | {test_name}")
    if message:
        print(f"         | {message}")

def check_python_version() -> Tuple[bool, str]:
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"Python {version.major}.{version.minor} (requires 3.8+)"

def check_dependencies() -> List[Tuple[str, bool, str]]:
    """Check if all required packages are installed."""
    results = []
    
    packages = [
        ("openai", "OpenAI API client"),
        ("dotenv", "python-dotenv package"),
        ("requests", "HTTP library"),
        ("bs4", "BeautifulSoup for web scraping"),
        ("pydantic", "Data validation"),
    ]
    
    for package, description in packages:
        try:
            __import__(package)
            results.append((description, True, f"Module '{package}' found"))
        except ImportError:
            results.append((description, False, f"Module '{package}' not found"))
    
    return results

def check_env_file() -> Tuple[bool, str]:
    """Check if .env file exists."""
    if os.path.exists('.env'):
        return True, ".env file found"
    else:
        return False, ".env file not found (copy from .env.example)"

def check_api_key() -> Tuple[bool, str]:
    """Check if API key is configured."""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "your_openai_api_key_here":
        # Don't log any part of the API key for security
        return True, "API key configured"
    else:
        return False, "API key not configured in .env"

def check_imports() -> List[Tuple[str, bool, str]]:
    """Check if all course modules can be imported."""
    results = []
    
    modules = [
        ("src.utils", "Utility functions"),
        ("src.module1_prompt_chaining", "Module 1: Prompt Chaining"),
        ("src.module2_tool_use", "Module 2: Tool Use"),
        ("src.module3_web_search", "Module 3: Web Search"),
        ("src.module4_agent_orchestration", "Module 4: Orchestration"),
        ("src.module5_advanced_agents", "Module 5: Advanced Agents"),
    ]
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            results.append((description, True, f"Import successful"))
        except ImportError as e:
            results.append((description, False, f"Import failed: {e}"))
    
    return results

def check_basic_functionality() -> Tuple[bool, str]:
    """Check if basic agent functionality works (without API call)."""
    try:
        from src.module1_prompt_chaining import PromptChain
        from src.module2_tool_use import calculate
        
        # Test a simple tool function
        result = calculate("add", 5, 3)
        if result == 8:
            return True, "Basic functionality working"
        else:
            return False, f"Unexpected result: {result}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Run all verification checks."""
    print_header("HSLU AGENTS COURSE - SETUP VERIFICATION")
    print("\nThis script verifies your environment is properly configured.")
    
    # Check Python version
    print_header("1. Python Version")
    python_passed, python_msg = check_python_version()
    print_result("Python version check", python_passed, python_msg)
    
    # Check dependencies
    print_header("2. Dependencies")
    deps = check_dependencies()
    all_deps_ok = all(passed for _, passed, _ in deps)
    for desc, passed, msg in deps:
        print_result(desc, passed, msg)
    
    # Check .env file
    print_header("3. Environment Configuration")
    env_passed, env_msg = check_env_file()
    print_result("Environment file", env_passed, env_msg)
    
    # Check API key (only if .env exists)
    if env_passed:
        api_passed, api_msg = check_api_key()
        print_result("OpenAI API key", api_passed, api_msg)
    else:
        print_result("OpenAI API key", False, "Skipped (no .env file)")
        api_passed = False
    
    # Check imports
    print_header("4. Module Imports")
    imports = check_imports()
    all_imports_ok = all(passed for _, passed, _ in imports)
    for desc, passed, msg in imports:
        print_result(desc, passed, msg)
    
    # Check basic functionality
    print_header("5. Basic Functionality")
    func_passed, func_msg = check_basic_functionality()
    print_result("Tool functions", func_passed, func_msg)
    
    # Summary
    print_header("SUMMARY")
    
    all_checks = [
        ("Python version", python_passed),
        ("Dependencies", all_deps_ok),
        ("Environment file", env_passed),
        ("API key", api_passed),
        ("Module imports", all_imports_ok),
        ("Basic functionality", func_passed),
    ]
    
    passed_count = sum(1 for _, passed in all_checks if passed)
    total_count = len(all_checks)
    
    print(f"\nPassed: {passed_count}/{total_count} checks")
    
    if passed_count == total_count:
        print("\n✓ Your environment is fully configured!")
        print("\nNext steps:")
        print("  1. Read QUICKSTART.md to run your first example")
        print("  2. Explore the modules in order (Module 1 → 5)")
        print("  3. Try the examples in the examples/ directory")
    else:
        print("\n✗ Some checks failed. Please address the issues above.")
        print("\nCommon fixes:")
        if not all_deps_ok:
            print("  - Run: pip install -r requirements.txt")
        if not env_passed:
            print("  - Run: cp .env.example .env")
        if not api_passed:
            print("  - Edit .env and add your OpenAI API key")
        if not all_imports_ok:
            print("  - Make sure you're in the repository root directory")
    
    print()
    return 0 if passed_count == total_count else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
