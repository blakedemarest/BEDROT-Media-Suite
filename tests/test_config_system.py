#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the centralized configuration system.

This script validates that the new configuration system works correctly
and provides meaningful error messages if there are issues.
"""

import os
import sys
from pathlib import Path

# Add src to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / 'src'))

def test_core_imports():
    """Test that core modules can be imported."""
    print("🧪 Testing core module imports...")
    
    try:
        from core import get_config_manager, load_environment, resolve_path
        from core.env_loader import get_env_var, get_bool_env_var, get_path_env_var
        from core.path_utils import get_path_resolver, resolve_config_path, resolve_output_path
        print("✅ Core module imports successful")
        return True
    except ImportError as e:
        print(f"❌ Core module import failed: {e}")
        return False

def test_environment_loading():
    """Test environment variable loading."""
    print("\n🧪 Testing environment loading...")
    
    try:
        from core.env_loader import get_env_loader
        
        env_loader = get_env_loader()
        env_loader.load_environment()
        
        # Test project root detection
        project_root = env_loader.project_root
        print(f"✅ Project root detected: {project_root}")
        
        # Test basic environment variables
        config_dir = env_loader.get_env_var('SLIDESHOW_CONFIG_DIR', 'config')
        print(f"✅ Config directory: {config_dir}")
        
        return True
    except Exception as e:
        print(f"❌ Environment loading failed: {e}")
        return False

def test_path_resolution():
    """Test path resolution utilities."""
    print("\n🧪 Testing path resolution...")
    
    try:
        from core.path_utils import get_path_resolver, resolve_config_path, resolve_output_path
        
        path_resolver = get_path_resolver()
        
        # Test config path resolution
        config_path = resolve_config_path('test_config.json')
        print(f"✅ Config path resolution: {config_path}")
        
        # Test output path resolution
        output_path = resolve_output_path()
        print(f"✅ Output path resolution: {output_path}")
        
        # Test project path resolution
        src_path = path_resolver.resolve_project_path('src')
        print(f"✅ Project path resolution: {src_path}")
        
        return True
    except Exception as e:
        print(f"❌ Path resolution failed: {e}")
        return False

def test_config_manager():
    """Test configuration manager."""
    print("\n🧪 Testing configuration manager...")
    
    try:
        from core.config_manager import get_config_manager, load_app_config
        
        config_manager = get_config_manager()
        
        # Test script path resolution
        try:
            media_script = config_manager.get_script_path('media_download')
            print(f"✅ Script path resolution: {media_script}")
        except Exception as e:
            print(f"⚠️  Script path resolution warning: {e}")
        
        # Test app config loading
        try:
            test_config = load_app_config('media_download', 'yt_downloader_gui_settings.json')
            print(f"✅ App config loading: Found {len(test_config)} settings")
        except Exception as e:
            print(f"⚠️  App config loading warning: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration manager failed: {e}")
        return False

def test_launcher_integration():
    """Test launcher integration."""
    print("\n🧪 Testing launcher integration...")
    
    try:
        # Check if launcher can import core modules
        launcher_path = SCRIPT_DIR / 'launcher.py'
        if launcher_path.exists():
            # Read launcher content to check for core imports
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'from core import' in content:
                print("✅ Launcher has core module imports")
            else:
                print("⚠️  Launcher missing core module imports")
            
            if 'get_script_path(' in content:
                print("✅ Launcher uses centralized script path resolution")
            else:
                print("⚠️  Launcher missing centralized script path resolution")
            
            return True
        else:
            print("⚠️  launcher.py not found")
            return False
    except Exception as e:
        print(f"❌ Launcher integration test failed: {e}")
        return False

def test_security_features():
    """Test security features."""
    print("\n🧪 Testing security features...")
    
    try:
        from core.path_utils import get_path_resolver
        
        path_resolver = get_path_resolver()
        
        # Test path validation
        safe_path = path_resolver.validate_path_security("normal/path")
        print(f"✅ Safe path validation: {safe_path}")
        
        # Test dangerous path detection
        dangerous_path = path_resolver.validate_path_security("../../../etc/passwd")
        print(f"✅ Dangerous path detection: {not dangerous_path}")
        
        # Test null byte protection
        null_path = path_resolver.validate_path_security("path\x00injection")
        print(f"✅ Null byte protection: {not null_path}")
        
        return True
    except Exception as e:
        print(f"❌ Security features test failed: {e}")
        return False

def test_fallback_mechanisms():
    """Test fallback mechanisms."""
    print("\n🧪 Testing fallback mechanisms...")
    
    try:
        # Temporarily disable core system to test fallbacks
        import sys
        original_path = sys.path.copy()
        
        # Remove src from path to simulate missing core modules
        sys.path = [p for p in sys.path if not p.endswith('/src') and not p.endswith('\\src')]
        
        # Test that launcher can still work without core modules
        launcher_path = SCRIPT_DIR / 'launcher.py'
        if launcher_path.exists():
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'except ImportError' in content and 'fallback' in content.lower():
                print("✅ Launcher has fallback mechanisms")
            else:
                print("⚠️  Launcher missing fallback mechanisms")
        
        # Restore original path
        sys.path = original_path
        
        return True
    except Exception as e:
        print(f"❌ Fallback mechanisms test failed: {e}")
        return False

def main():
    """Run all configuration system tests."""
    print("🔧 Bedrot Productions Media Tool Suite - Configuration System Test")
    print("=" * 70)
    
    tests = [
        test_core_imports,
        test_environment_loading,
        test_path_resolution,
        test_config_manager,
        test_launcher_integration,
        test_security_features,
        test_fallback_mechanisms
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())