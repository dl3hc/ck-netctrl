# -----------------------------------------------------------------------------
# Christian-Koppler Control Software (ck-netctrl)
# Copyright (C) 2025 dl3hc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version, **with the following restriction**:
#
# Non-Commercial Use Only:
# This software may not be used for commercial purposes.
# Commercial purposes include selling, licensing, or using the software
# to provide paid services.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details:
# https://www.gnu.org/licenses/
#
# Additional notes:
# 1. Any modifications or derived works must also be released under
#    this same license (GPLv3 + Non-Commercial).
# 2. Redistribution of modified versions must also make the source code
#    available under this license.
# -----------------------------------------------------------------------------

"""
Main entry point for the Christian-Koppler Control Software (ck-netctrl).

This module initializes the Qt application and launches the main GUI window.

Usage:
    python main.py

Modules:
    gui: Contains the MainWindow class for the GUI.
"""

from PyQt6.QtWidgets import QApplication
from gui import MainWindow
import sys

def main():
    """
    Initializes and runs the Qt application.

    This function:
    1. Creates a QApplication instance.
    2. Instantiates the MainWindow.
    3. Shows the main window.
    4. Starts the Qt event loop.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
