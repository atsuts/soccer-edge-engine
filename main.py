#!/usr/bin/env python3
"""
# =============================================================================
# SOCCER EDGE ENGINE - BACKUP LAUNCHER
# =============================================================================
# This is a BACKUP launcher for Soccer Edge Engine project.
# Use soccer_gui.py as the main launcher instead.
# =============================================================================

import sys
import os

# Add current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Launch the Soccer Edge Engine GUI"""
    try:
        # Import and run the main GUI
        from soccer_gui import main as gui_main
        print("Starting Soccer Edge Engine...")
        gui_main()
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Please ensure all required files are present.")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"Error starting Soccer Edge Engine: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
