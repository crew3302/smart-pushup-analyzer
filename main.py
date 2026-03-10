"""
AI-Based Push-Up Form Analyzer
Main entry point.

Launch this file to start the application:
    python main.py
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
