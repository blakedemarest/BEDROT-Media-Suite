#!/usr/bin/env python3
"""Test if PyQt5 is working properly."""

import sys

print("Testing PyQt5...")

try:
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
    print("✓ PyQt5 imports successful")
except ImportError as e:
    print(f"✗ PyQt5 import failed: {e}")
    sys.exit(1)

def main():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("PyQt5 Test")
    window.resize(300, 150)
    
    layout = QVBoxLayout()
    
    label = QLabel("PyQt5 is working!")
    label.setStyleSheet("font-size: 16px; padding: 20px;")
    layout.addWidget(label)
    
    button = QPushButton("Close")
    button.clicked.connect(window.close)
    layout.addWidget(button)
    
    window.setLayout(layout)
    window.show()
    
    print("✓ Window created successfully")
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())