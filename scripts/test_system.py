"""
System Test Script
Verifies that all components are properly installed and configured
"""
import sys
import os
from typing import List, Tuple


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_test(name: str, passed: bool, message: str = ""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {name}")
    if message:
        print(f"         {message}")


def test_python_version() -> Tuple[bool, str]:
    """Test Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)"


def test_import(module_name: str) -> Tuple[bool, str]:
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        return True, f"{module_name} imported successfully"
    except ImportError as e:
        return False, f"{module_name} import failed: {str(e)}"


def test_environment_file() -> Tuple[bool, str]:
    """Test if .env file exists"""
    if os.path.exists('.env'):
        return True, ".env file found"
    return False, ".env file not found (copy from .env.example)"


def test_openai_api_key() -> Tuple[bool, str]:
    """Test if OpenAI API key is configured"""
    try:
        from chatbot.utils.config import settings
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            return True, "OpenAI API key configured"
        return False, "OpenAI API key not configured in .env"
    except Exception as e:
        return False, f"Error loading config: {str(e)}"


def test_directories() -> Tuple[bool, str]:
    """Test if required directories exist"""
    required_dirs = ['storage', 'reports', 'uploads', 'logs']
    missing = [d for d in required_dirs if not os.path.exists(d)]
    
    if not missing:
        return True, "All required directories exist"
    return False, f"Missing directories: {', '.join(missing)}"


def test_module_files() -> Tuple[bool, str]:
    """Test if all module files exist"""
    required_files = [
        'config.py', 'utils.py', 'ingestion.py', 'retrievers.py',
        'states.py', 'fit_score.py', 'agent.py', 'report_generator.py',
        'verification.py', 'main.py'
    ]
    missing = [f for f in required_files if not os.path.exists(f)]
    
    if not missing:
        return True, f"All {len(required_files)} module files present"
    return False, f"Missing files: {', '.join(missing)}"


def test_docker_compose() -> Tuple[bool, str]:
    """Test if docker-compose.yml exists"""
    if os.path.exists('docker-compose.yml'):
        return True, "docker-compose.yml found"
    return False, f"Missing directories: {', '.join(missing)}"


def run_all_tests():
    """Run all system tests"""
    print_header("Cleo RAG Agent - System Tests")
    
    tests = [
        ("Python Version", test_python_version),
        ("Environment File", test_environment_file),
        ("OpenAI API Key", test_openai_api_key),
        ("Required Directories", test_directories),
        ("Module Files", test_module_files),
        ("Docker Compose File", test_docker_compose),
    ]
    
    # Import tests (only if basics are working)
    import_tests = [
        ("dotenv", "python-dotenv"),
        ("pydantic", "pydantic"),
        ("loguru", "loguru"),
        ("langchain", "langchain"),
        ("langchain_openai", "langchain-openai"),
        # ("pymilvus", "pymilvus"),
        ("fitz", "PyMuPDF"),
        ("openai", "openai"),
        ("reportlab", "reportlab"),
    ]
    
    # Optional tests (may fail if services not running)
    optional_tests = [
        # ("Milvus Connection", test_milvus_connection),
        # ("Knowledge Base", test_knowledge_base),
    ]
    
    results = []
    
    # Run basic tests
    print("\n📋 Basic Configuration Tests:")
    for name, test_func in tests:
        passed, message = test_func()
        print_test(name, passed, message)
        results.append((name, passed))
    
    # Run import tests
    print("\n📦 Python Package Tests:")
    for package_name, display_name in import_tests:
        passed, message = test_import(package_name)
        print_test(f"Import {display_name}", passed, message)
        results.append((f"Import {display_name}", passed))
    
    # Run optional tests
    print("\n🔧 Optional Service Tests:")
    for name, test_func in optional_tests:
        passed, message = test_func()
        print_test(name, passed, message)
        # Don't count optional tests in failure count
    
    # Summary
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    failed = total - passed
    
    print(f"\n  Total Tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failed == 0:
        print("\n  ✓ All tests passed! System is ready.")
        print("\n  Next steps:")
        print("    1. Ensure Milvus is running: docker-compose up -d")
        print("    2. Create sample docs: python create_sample_docs.py")
        print("    3. Setup knowledge base: python setup_knowledge_base.py")
        print("    4. Run demo: python demo_conversation.py")
    else:
        print("\n  ✗ Some tests failed. Please fix the issues above.")
        print("\n  Common fixes:")
        print("    • Install dependencies: pip install -r requirements.txt")
        print("    • Create .env file: cp .env.example .env")
        print("    • Add OpenAI API key to .env file")
        print("    • Create directories: python -c 'from chatbot.utils.config import ensure_directories; ensure_directories()'")
    
    print("\n" + "="*70 + "\n")
    
    return failed == 0


def main():
    """Main entry point"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTests failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
