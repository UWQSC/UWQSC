"""
This file stores the global constants used in the entire project.
"""

import os.path

# Commonly used path names
COMMON_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(COMMON_DIR)
PROJECT_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")

# Errors
INTERFACE_NOT_IMPLEMENTED_ERROR = RuntimeError("Method Not Implemented")
