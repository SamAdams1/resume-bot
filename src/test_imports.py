"""
Import verification test to ensure no circular imports or missing dependencies.
Run this from the src directory: python test_imports.py
"""

import sys
import os
import traceback

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

test_results = []

def test_import(module_name):
    """Test if a module can be imported without errors."""
    try:
        __import__(module_name)
        test_results.append((module_name, "✓ OK", None))
        print(f"✓ {module_name}")
        return True
    except Exception as e:
        test_results.append((module_name, "✗ FAILED", str(e)))
        print(f"✗ {module_name}: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing module imports...\n")
    
    # Test in order of dependencies (config must be first)
    test_import("config")
    test_import("db_write")
    test_import("parse_jobs")
    test_import("search")
    test_import("main")
    
    print("\n" + "="*60)
    print("IMPORT TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, status, _ in test_results if status == "✓ OK")
    total = len(test_results)
    
    for module, status, error in test_results:
        print(f"{status} - {module}")
        if error:
            print(f"   Error: {error}\n")
    
    print("="*60)
    print(f"Results: {passed}/{total} modules imported successfully")
    
    if passed == total:
        print("✓ All imports successful! No circular dependencies detected.")
        sys.exit(0)
    else:
        print("✗ Some imports failed. Fix errors above.")
        sys.exit(1)
