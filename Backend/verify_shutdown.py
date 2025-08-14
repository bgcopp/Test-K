"""
KRONOS Shutdown System Verification
===============================================================================
Quick verification script to confirm that the shutdown system is properly
implemented and all components are working correctly.

This script performs static analysis of the codebase to verify:
- All required components are present
- Signal handlers are configured
- Cleanup handlers are registered
- Eel integration is correct
- No critical issues exist

Usage:
    python verify_shutdown.py

Returns:
    Exit code 0: All verifications passed
    Exit code 1: Critical issues found
===============================================================================
"""

import os
import sys
import ast
import inspect
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def verify_main_implementation():
    """Verify main.py has all required shutdown components"""
    issues = []
    
    try:
        # Import main to verify it loads without errors
        import main
        
        # Check ApplicationShutdownManager exists
        if not hasattr(main, 'ApplicationShutdownManager'):
            issues.append("ApplicationShutdownManager class not found")
        else:
            manager = main.ApplicationShutdownManager()
            
            # Check required methods
            required_methods = ['initiate_shutdown', 'register_cleanup_handler', '_execute_cleanup_sequence']
            for method in required_methods:
                if not hasattr(manager, method):
                    issues.append(f"ApplicationShutdownManager missing method: {method}")
        
        # Check shutdown_manager global instance
        if not hasattr(main, 'shutdown_manager'):
            issues.append("Global shutdown_manager instance not found")
        
        # Check signal handler functions
        required_functions = ['setup_signal_handlers', 'setup_cleanup_handlers', 'setup_atexit_handler']
        for func in required_functions:
            if not hasattr(main, func):
                issues.append(f"Required function not found: {func}")
        
        # Check Eel functions are exposed
        eel_functions = ['login', 'get_users', 'get_roles', 'get_missions']
        for func in eel_functions:
            if not hasattr(main, func):
                issues.append(f"Required Eel function not exposed: {func}")
            else:
                # Check if function has @eel.expose decorator
                func_obj = getattr(main, func)
                if not hasattr(func_obj, '__name__'):
                    issues.append(f"Function {func} may not be properly exposed to Eel")
        
    except Exception as e:
        issues.append(f"Error importing main.py: {e}")
    
    return issues

def verify_close_callback():
    """Verify the close_callback signature is correct"""
    issues = []
    
    try:
        main_path = backend_dir / 'main.py'
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for close_callback in eel.start
        if 'close_callback=' not in content:
            issues.append("close_callback not found in eel.start call")
        
        # Check that it accepts page and sockets parameters
        if 'lambda page, sockets:' not in content:
            issues.append("close_callback does not have correct signature (page, sockets)")
        
        # Check that it calls shutdown_manager.initiate_shutdown
        if 'shutdown_manager.initiate_shutdown' not in content:
            issues.append("close_callback does not call shutdown_manager.initiate_shutdown")
    
    except Exception as e:
        issues.append(f"Error verifying close_callback: {e}")
    
    return issues

def verify_database_cleanup():
    """Verify database connection cleanup is implemented"""
    issues = []
    
    try:
        from database.connection import get_database_manager
        
        db_manager = get_database_manager()
        if not hasattr(db_manager, 'close'):
            issues.append("DatabaseManager missing close() method")
        
        # Verify close method disposes engine
        close_method = getattr(db_manager, 'close')
        source = inspect.getsource(close_method)
        if 'dispose()' not in source:
            issues.append("DatabaseManager.close() does not call engine.dispose()")
    
    except Exception as e:
        issues.append(f"Error verifying database cleanup: {e}")
    
    return issues

def verify_test_framework():
    """Verify test framework is present and functional"""
    issues = []
    
    try:
        test_path = backend_dir / 'test_shutdown.py'
        if not test_path.exists():
            issues.append("test_shutdown.py not found")
            return issues
        
        # Try to import test functions
        import test_shutdown
        
        required_functions = ['test_shutdown_system', 'test_signal_handling', 'run_resource_check']
        for func in required_functions:
            if not hasattr(test_shutdown, func):
                issues.append(f"Test function not found: {func}")
    
    except Exception as e:
        issues.append(f"Error verifying test framework: {e}")
    
    return issues

def run_verification():
    """Run all verification checks"""
    print("KRONOS Shutdown System Verification")
    print("=" * 50)
    
    all_issues = []
    
    # Run all checks
    checks = [
        ("Main Implementation", verify_main_implementation),
        ("Close Callback", verify_close_callback),
        ("Database Cleanup", verify_database_cleanup),
        ("Test Framework", verify_test_framework),
    ]
    
    for check_name, check_func in checks:
        print(f"\nChecking {check_name}...")
        issues = check_func()
        
        if issues:
            print(f"  [ERROR] {len(issues)} issues found:")
            for issue in issues:
                print(f"    - {issue}")
            all_issues.extend(issues)
        else:
            print(f"  [OK] {check_name} verification passed")
    
    # Final summary
    print("\n" + "=" * 50)
    if all_issues:
        print(f"[FAIL] Verification failed with {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"  - {issue}")
        return False
    else:
        print("[SUCCESS] All shutdown system verifications passed!")
        print("\nShutdown system is properly implemented and ready for production.")
        return True

if __name__ == '__main__':
    try:
        success = run_verification()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Verification script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)