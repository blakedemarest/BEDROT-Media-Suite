# Modularization Guidelines for LLM Agents

## Overview

This document provides comprehensive guidelines for LLM agents to transform monolithic Python scripts into clean, reusable, modular packages within the slideshow_editor repository. The guidelines are based on successful modularization patterns observed in the `reel_tracker` and `random_slideshow` modules.

> Note: The `random_slideshow` package was archived on 2025-10-28; examples remain for historical reference.

## 🎯 Core Principles

### 1. **Single Responsibility Principle**
- Each module should have one clear, well-defined purpose
- Separate concerns into distinct files (UI, business logic, configuration, utilities)
- Keep classes focused on a single responsibility

### 2. **Dependency Injection**
- Pass dependencies through constructors or method parameters
- Avoid tight coupling between modules
- Make testing and maintenance easier

### 3. **Lazy Loading**
- Import heavy dependencies only when needed
- Use factory functions for optional components
- Minimize startup time and memory usage

## 📁 Directory Structure Patterns

### ✅ Good: Modular Package Structure
```
src/
├── package_name/
│   ├── __init__.py          # Package exports and lazy imports
│   ├── main_app.py          # Main application/GUI class
│   ├── config_manager.py    # Configuration handling
│   ├── core_logic.py        # Core business logic
│   ├── worker_threads.py    # Background processing
│   ├── dialogs.py           # UI dialogs and forms
│   ├── utils.py             # Utility functions
│   └── README.md            # Module documentation
├── package_name_entry.py    # Modular entry point script
└── old_monolithic_script.py # Keep for reference during transition
```

### ❌ Bad: Monolithic Structure
```
src/
├── huge_script.py           # 500+ lines mixing UI, logic, config
├── another_big_script.py    # Similar issues
└── utilities_everywhere.py  # Shared code duplicated
```

## 🔧 Step-by-Step Modularization Process

### Phase 1: Analysis and Planning
1. **Identify Functional Areas**
   - GUI/UI components
   - Configuration management
   - Core business logic
   - File I/O operations
   - Background processing
   - Utility functions

2. **Map Dependencies**
   - External libraries (PyQt5, PIL, etc.)
   - Internal cross-references
   - Configuration requirements
   - Shared utilities

3. **Plan Module Boundaries**
   - Group related functionality
   - Identify shared components
   - Design clean interfaces

### Phase 2: Module Creation

#### Step 1: Create Package Directory
```python
# Create directory structure
mkdir src/new_package_name
touch src/new_package_name/__init__.py
```

#### Step 2: Extract Configuration Management
```python
# config_manager.py
class ConfigManager:
    """Handles all configuration loading, saving, and management."""
    
    def __init__(self, config_file="config/package_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from JSON file or create defaults."""
        # Implementation here
        pass
    
    def save_config(self, config_data=None):
        """Save current configuration to file."""
        # Implementation here
        pass
```

#### Step 3: Extract Core Business Logic
```python
# core_logic.py
class CoreProcessor:
    """Contains the main business logic separated from UI."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def process_data(self, input_data):
        """Main processing function."""
        # Implementation here
        pass
```

#### Step 4: Extract UI Components
```python
# main_app.py
from PyQt5.QtWidgets import QWidget
from .config_manager import ConfigManager
from .core_logic import CoreProcessor

class MainApplication(QWidget):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.processor = CoreProcessor(self.config_manager)
        self.setup_ui()
```

#### Step 5: Extract Worker Threads
```python
# worker_threads.py
from PyQt5.QtCore import QThread, pyqtSignal

class ProcessingWorker(QThread):
    """Background processing thread."""
    
    progress_updated = pyqtSignal(str)
    operation_completed = pyqtSignal(dict)
    
    def __init__(self, processor, data):
        super().__init__()
        self.processor = processor
        self.data = data
```

#### Step 6: Create Package Exports
```python
# __init__.py
"""
Package Name - A modular application for [description].

This package provides:
- [Feature 1]
- [Feature 2]
- [Feature 3]
"""

# Import core classes
from .config_manager import ConfigManager
from .core_logic import CoreProcessor

# Lazy imports for optional components
def get_main_app():
    """Lazy import for MainApplication to avoid PyQt5 dependency issues."""
    from .main_app import MainApplication
    return MainApplication

def get_processing_worker():
    """Lazy import for ProcessingWorker to avoid PyQt5 dependency issues."""
    from .worker_threads import ProcessingWorker
    return ProcessingWorker

__version__ = "1.0.0"
__author__ = "Bedrot Productions"

__all__ = [
    "ConfigManager",
    "CoreProcessor", 
    "get_main_app",
    "get_processing_worker"
]
```

#### Step 7: Create Entry Point Script
```python
# package_name_modular.py
"""
Package Name - Modular Entry Point

This is the main entry point for the modular package application.
It imports and runs the application from the package.
"""

if __name__ == "__main__":
    from package_name.main_app import main
    main()
```

### Phase 3: Migration and Testing

#### Step 1: Gradual Migration
- Keep original monolithic script as reference
- Test each module individually
- Ensure feature parity

#### Step 2: Update Imports
- Replace hardcoded paths with relative imports
- Use dependency injection instead of global variables
- Handle import errors gracefully

#### Step 3: Configuration Migration
- Move config files to standardized locations
- Ensure backward compatibility
- Add migration helpers if needed

## 📋 Code Quality Standards

### File Organization
```python
# File header with encoding and docstring
# -*- coding: utf-8 -*-
"""
Module Name - Brief Description

Detailed description of module purpose and functionality.
"""

# Standard library imports
import os
import json

# Third-party imports
from PyQt5.QtWidgets import QWidget

# Local imports
from .config_manager import ConfigManager
from .utils import safe_print
```

### Class Structure
```python
class ExampleClass:
    """
    Brief description of class purpose.
    
    Longer description of functionality, usage, and important notes.
    """
    
    def __init__(self, required_param, optional_param=None):
        """Initialize the class with required dependencies."""
        self.required_param = required_param
        self.optional_param = optional_param
        self._private_var = None
    
    def public_method(self, param):
        """Public method with clear documentation."""
        # Implementation
        pass
    
    def _private_method(self):
        """Private helper method."""
        # Implementation
        pass
```

### Error Handling
```python
from .utils import safe_print

def robust_function(param):
    """Function with proper error handling."""
    try:
        # Main logic here
        result = process_param(param)
        return result
    except SpecificException as e:
        safe_print(f"Specific error in robust_function: {e}")
        return None
    except Exception as e:
        safe_print(f"Unexpected error in robust_function: {e}")
        return None
```

## 🚀 Real-World Examples

### Example 1: From Monolithic to Modular

#### Before: Monolithic Script (random_slideshow.py)
```python
# 500+ lines containing:
# - Configuration loading/saving
# - Image processing functions
# - PyQt5 GUI setup
# - Worker thread implementation
# - All mixed together in one file
```

#### After: Modular Structure (random_slideshow/)
```
random_slideshow/
├── __init__.py              # Package exports with lazy imports
├── config_manager.py        # Configuration handling
├── image_processor.py       # Image processing logic
├── main_app.py             # GUI application
├── slideshow_worker.py     # Background processing
└── main.py                 # Entry point function
```

### Example 2: Successful Modular Package (reel_tracker/)
```
reel_tracker/
├── __init__.py              # Clean package exports
├── main_app.py             # Main application window
├── config_manager.py       # Configuration management
├── reel_dialog.py          # Form dialogs
├── file_organization_dialog.py  # Specialized dialogs
├── file_organizer.py       # File operations
├── media_randomizer.py     # Media processing
├── custom_item_manager.py  # Custom functionality
├── utils.py                # Shared utilities
└── README.md               # Documentation
```

## 📝 Migration Checklist

### Pre-Migration Analysis
- [ ] Identify all functional areas in monolithic script
- [ ] Map external dependencies (PyQt5, PIL, etc.)
- [ ] Document current configuration approach
- [ ] List all entry points and main functions

### Module Creation
- [ ] Create package directory with `__init__.py`
- [ ] Extract configuration management
- [ ] Separate core business logic from UI
- [ ] Create worker thread modules
- [ ] Extract utility functions
- [ ] Create dialog/UI modules

### Integration
- [ ] Implement lazy imports in `__init__.py`
- [ ] Create modular entry point script
- [ ] Update import statements
- [ ] Handle dependency injection
- [ ] Test module isolation

### Quality Assurance
- [ ] Ensure feature parity with original script
- [ ] Test error handling and edge cases
- [ ] Verify configuration migration works
- [ ] Check performance impact
- [ ] Update documentation

### Cleanup
- [ ] Remove duplicate code
- [ ] Standardize naming conventions
- [ ] Add proper docstrings
- [ ] Create module README
- [ ] Archive original monolithic script

## 🛠️ Common Patterns

### Configuration Management Pattern
```python
class ConfigManager:
    def __init__(self, config_file="config/app_config.json"):
        self.config_file = config_file
        self.config_dir = os.path.dirname(config_file)
        self.config = self.load_config()
    
    def load_config(self):
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
            
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                default_config = self.get_default_config()
                self.save_config(default_config)
                return default_config
        except Exception as e:
            safe_print(f"Error loading config: {e}")
            return self.get_default_config()
```

### Worker Thread Pattern
```python
class ProcessingWorker(QThread):
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    operation_completed = pyqtSignal(dict)  # results
    
    def __init__(self, processor, data):
        super().__init__()
        self.processor = processor
        self.data = data
        self.results = {}
    
    def run(self):
        try:
            self.results = self.processor.process_batch(
                self.data, 
                progress_callback=self.progress_callback
            )
            self.operation_completed.emit(self.results)
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            self.operation_completed.emit(error_result)
    
    def progress_callback(self, current, total, message):
        self.progress_updated.emit(current, total, message)
```

### Lazy Import Pattern
```python
# In __init__.py
def get_main_app():
    """Lazy import for MainApplication to avoid PyQt5 dependency issues."""
    from .main_app import MainApplication
    return MainApplication

def get_worker_class():
    """Lazy import for Worker to avoid heavy dependencies.""" 
    from .worker_threads import ProcessingWorker
    return ProcessingWorker
```

## 🎯 Success Metrics

A successful modularization should achieve:

1. **Maintainability**: Each module has a clear, single purpose
2. **Testability**: Components can be tested in isolation
3. **Reusability**: Modules can be imported and used independently
4. **Scalability**: New features can be added without major refactoring
5. **Performance**: No significant performance degradation
6. **Documentation**: Clear module interfaces and usage examples

## 🚨 Common Pitfalls to Avoid

### Over-Modularization
- Don't create modules for every single function
- Avoid circular dependencies
- Keep related functionality together

### Under-Modularization
- Don't leave large, multi-purpose modules
- Separate UI from business logic
- Extract configuration management

### Import Issues
- Avoid absolute imports within the package
- Handle missing dependencies gracefully
- Use lazy imports for heavy dependencies

### Configuration Problems
- Don't hardcode paths in modules
- Make configuration backward-compatible
- Provide sensible defaults

## 📚 Additional Resources

- Python Package Documentation: [docs.python.org](https://docs.python.org/3/tutorial/modules.html)
- PyQt5 Best Practices: Focus on separating UI from logic
- Clean Code Principles: Single Responsibility, Open/Closed, etc.

---

## 🏷️ Template Checklist for LLM Agents

When modularizing a script, use this checklist:

1. **Analyze** the monolithic script structure
2. **Plan** the module boundaries and dependencies  
3. **Create** package directory with proper `__init__.py`
4. **Extract** configuration management first
5. **Separate** core logic from UI components
6. **Implement** worker threads for background processing
7. **Add** proper error handling and logging
8. **Create** modular entry point script
9. **Test** feature parity and performance
10. **Document** the new modular structure

Remember: **Gradual migration with testing at each step is key to successful modularization.**
