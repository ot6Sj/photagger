"""Launcher script — run from project root: python run.py"""
import sys
import os

# Add src to path so the package can be found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from photagger.__main__ import main

if __name__ == "__main__":
    main()
