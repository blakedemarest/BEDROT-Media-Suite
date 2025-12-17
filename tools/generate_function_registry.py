#!/usr/bin/env python3
"""
Function Registry Generator for Bedrot Productions Media Tool Suite
Scans all Python files and extracts functions, classes, and methods with metadata.
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import inspect

class FunctionRegistryGenerator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.registry = {}
        
    def extract_docstring(self, node) -> str:
        """Extract docstring from an AST node."""
        if (isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and 
            node.body and 
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            return node.body[0].value.value.strip()
        return ""
    
    def get_function_signature(self, node: ast.FunctionDef) -> List[str]:
        """Extract function arguments from AST node."""
        args = []
        
        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                try:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                except:
                    pass
            args.append(arg_str)
        
        # *args
        if node.args.vararg:
            vararg_str = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                try:
                    vararg_str += f": {ast.unparse(node.args.vararg.annotation)}"
                except:
                    pass
            args.append(vararg_str)
        
        # **kwargs
        if node.args.kwarg:
            kwarg_str = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                try:
                    kwarg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
                except:
                    pass
            args.append(kwarg_str)
        
        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            arg_str = arg.arg
            if arg.annotation:
                try:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                except:
                    pass
            args.append(arg_str)
        
        return args
    
    def get_class_info(self, node: ast.ClassDef, file_path: str) -> Dict[str, Any]:
        """Extract class information."""
        bases = []
        for base in node.bases:
            try:
                bases.append(ast.unparse(base))
            except:
                bases.append(str(base))
        
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = {
                    "name": item.name,
                    "args": self.get_function_signature(item),
                    "docstring": self.extract_docstring(item),
                    "line": item.lineno,
                    "is_async": isinstance(item, ast.AsyncFunctionDef),
                    "is_property": any(
                        isinstance(decorator, ast.Name) and decorator.id == "property"
                        for decorator in item.decorator_list
                    ),
                    "is_staticmethod": any(
                        isinstance(decorator, ast.Name) and decorator.id == "staticmethod"
                        for decorator in item.decorator_list
                    ),
                    "is_classmethod": any(
                        isinstance(decorator, ast.Name) and decorator.id == "classmethod"
                        for decorator in item.decorator_list
                    )
                }
                methods.append(method_info)
        
        return {
            "type": "class",
            "name": node.name,
            "file": str(file_path),
            "line": node.lineno,
            "docstring": self.extract_docstring(node),
            "bases": bases,
            "methods": methods,
            "language": "python"
        }
    
    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """Scan a single Python file and extract all functions and classes."""
        file_info = {
            "functions": {},
            "classes": {},
            "imports": [],
            "constants": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        file_info["imports"].append({
                            "module": alias.name,
                            "alias": alias.asname,
                            "type": "import"
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        file_info["imports"].append({
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "type": "from_import"
                        })
            
            # Extract top-level definitions
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = node.name
                    file_info["functions"][func_name] = {
                        "type": "function",
                        "name": func_name,
                        "file": str(file_path),
                        "line": node.lineno,
                        "args": self.get_function_signature(node),
                        "docstring": self.extract_docstring(node),
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "language": "python"
                    }
                
                elif isinstance(node, ast.ClassDef):
                    class_name = node.name
                    file_info["classes"][class_name] = self.get_class_info(node, file_path)
                
                elif isinstance(node, ast.Assign):
                    # Extract module-level constants
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id.isupper():  # Convention for constants
                                try:
                                    value = ast.literal_eval(node.value)
                                    if isinstance(value, set):
                                        value = sorted(value)
                                    elif isinstance(value, tuple):
                                        value = list(value)
                                    file_info["constants"].append({
                                        "name": target.id,
                                        "value": value,
                                        "line": node.lineno
                                    })
                                except:
                                    file_info["constants"].append({
                                        "name": target.id,
                                        "value": "<complex_expression>",
                                        "line": node.lineno
                                    })
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return file_info
        
        return file_info
    
    def generate_registry(self, python_files: List[str]) -> Dict[str, Any]:
        """Generate complete function registry."""
        registry = {
            "metadata": {
                "generated_at": str(Path(__file__).stat().st_mtime),
                "project_root": str(self.project_root),
                "total_files": 0,
                "total_functions": 0,
                "total_classes": 0,
                "total_methods": 0
            },
            "files": {},
            "functions": {},
            "classes": {},
            "duplicates": [],
            "statistics": {}
        }
        
        function_names = {}
        class_names = {}
        
        for py_file in python_files:
            file_path = Path(py_file)
            relative_path = str(file_path.relative_to(self.project_root))
            
            print(f"Scanning: {relative_path}")
            file_info = self.scan_file(file_path)
            
            registry["files"][relative_path] = file_info
            registry["metadata"]["total_files"] += 1
            
            # Add functions to global registry
            for func_name, func_info in file_info["functions"].items():
                full_key = f"{relative_path}::{func_name}"
                registry["functions"][full_key] = func_info
                registry["metadata"]["total_functions"] += 1
                
                # Track duplicates
                if func_name in function_names:
                    function_names[func_name].append(relative_path)
                else:
                    function_names[func_name] = [relative_path]
            
            # Add classes to global registry
            for class_name, class_info in file_info["classes"].items():
                full_key = f"{relative_path}::{class_name}"
                registry["classes"][full_key] = class_info
                registry["metadata"]["total_classes"] += 1
                registry["metadata"]["total_methods"] += len(class_info["methods"])
                
                # Track duplicates
                if class_name in class_names:
                    class_names[class_name].append(relative_path)
                else:
                    class_names[class_name] = [relative_path]
        
        # Identify duplicates
        for name, files in function_names.items():
            if len(files) > 1:
                registry["duplicates"].append({
                    "type": "function",
                    "name": name,
                    "files": files
                })
        
        for name, files in class_names.items():
            if len(files) > 1:
                registry["duplicates"].append({
                    "type": "class",
                    "name": name,
                    "files": files
                })
        
        # Generate statistics
        registry["statistics"] = {
            "files_by_directory": {},
            "functions_per_file": {},
            "classes_per_file": {},
            "duplicate_count": len(registry["duplicates"])
        }
        
        for file_path, file_info in registry["files"].items():
            directory = str(Path(file_path).parent)
            if directory not in registry["statistics"]["files_by_directory"]:
                registry["statistics"]["files_by_directory"][directory] = 0
            registry["statistics"]["files_by_directory"][directory] += 1
            
            registry["statistics"]["functions_per_file"][file_path] = len(file_info["functions"])
            registry["statistics"]["classes_per_file"][file_path] = len(file_info["classes"])
        
        return registry

def main():
    """Main execution function."""
    # Get the actual project root (parent of tools directory)
    project_root = Path(__file__).parent.parent.resolve()
    
    # Get all Python files from the entire project
    python_files = []
    for py_file in project_root.rglob("*.py"):
        # Skip virtual environments and temporary files
        if any(part.startswith(('.venv', 'venv', '__pycache__', '.git')) for part in py_file.parts):
            continue
        if 'temp/' in str(py_file):
            continue
        python_files.append(str(py_file))
    
    # Generate registry
    generator = FunctionRegistryGenerator(project_root)
    registry = generator.generate_registry(python_files)
    
    # Save to file at repo root
    output_file = project_root / "bedrot_media_suite_function_registry.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    
    print(f"\nFunction Registry Generated:")
    print(f"- Output file: {output_file}")
    print(f"- Files scanned: {registry['metadata']['total_files']}")
    print(f"- Functions found: {registry['metadata']['total_functions']}")
    print(f"- Classes found: {registry['metadata']['total_classes']}")
    print(f"- Methods found: {registry['metadata']['total_methods']}")
    print(f"- Duplicates found: {registry['statistics']['duplicate_count']}")
    
    if registry["duplicates"]:
        print("\nDuplicate Names Found:")
        for dup in registry["duplicates"][:10]:  # Show first 10
            print(f"- {dup['type']}: '{dup['name']}' in {len(dup['files'])} files")

if __name__ == "__main__":
    main()
