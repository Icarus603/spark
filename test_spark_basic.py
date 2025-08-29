#!/usr/bin/env python3
"""
Basic test script to verify Spark Stage 1.1 implementation.

This script tests the core functionality without requiring full installation.
"""

import sys
import os
from pathlib import Path

# Add spark to Python path
spark_path = Path(__file__).parent / "libs" / "python" / "spark"
sys.path.insert(0, str(spark_path.parent))

def test_imports():
    """Test that all core modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        # Test core imports
        from spark import __version__
        print(f"  ✅ Spark version: {__version__}")
        
        from spark.cli.main import SparkCLI
        print("  ✅ CLI framework")
        
        from spark.core.config import SparkConfig
        print("  ✅ Configuration management")
        
        from spark.cli.terminal import SparkConsole
        print("  ✅ Terminal utilities")
        
        from spark.learning.git_patterns import GitPatternAnalyzer
        print("  ✅ Git pattern analysis")
        
        from spark.storage.patterns import PatternStorage
        print("  ✅ Storage layer")
        
        from spark.cli.commands.status import StatusCommand
        from spark.cli.commands.learn import LearnCommand
        print("  ✅ Command implementations")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_config():
    """Test configuration management."""
    print("\n⚙️  Testing configuration...")
    
    try:
        from spark.core.config import SparkConfig
        
        # Create temporary config
        config = SparkConfig(Path("/tmp/test_spark"))
        print("  ✅ Config creation")
        
        # Test validation
        errors = config.validate()
        print(f"  ✅ Config validation: {len(errors)} errors")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config error: {e}")
        return False

def test_cli_help():
    """Test CLI help functionality."""
    print("\n💬 Testing CLI help...")
    
    try:
        from spark.cli.main import SparkCLI
        
        cli = SparkCLI()
        result = cli._help_command([])
        print(f"  ✅ Help command returned: {result}")
        
        result = cli._version_command([])
        print(f"  ✅ Version command returned: {result}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ CLI error: {e}")
        return False

def test_terminal():
    """Test terminal formatting."""
    print("\n🎨 Testing terminal formatting...")
    
    try:
        from spark.cli.terminal import SparkConsole, SparkTheme
        
        console = SparkConsole()
        theme = SparkTheme()
        
        print("  ✅ Console and theme creation")
        
        # Test some formatting
        test_data = {
            'confidence': 0.75,
            'days': 5,
            'recent_activity': {
                'patterns_detected': 10,
                'commits': 25,
                'files_modified': 15
            }
        }
        
        console.print_learning_progress(test_data)
        print("  ✅ Progress display")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Terminal error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Spark Stage 1.1 Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_cli_help,
        test_terminal
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Stage 1.1 implementation is working.")
        print("\n💡 Next steps:")
        print("  1. Install dependencies: pip install rich tomli tomli-w")
        print("  2. Test with: python -m spark --help")
        print("  3. Initialize: python -m spark")
    else:
        print("⚠️  Some tests failed. Check implementation.")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())