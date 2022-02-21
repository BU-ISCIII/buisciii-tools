!/usr/bin/env python
"""
Common utility function for bu-isciii package.
"""

import os

def rich_force_colors():
    """
    Check if any environment variables are set to force Rich to use coloured output
    """
    if os.getenv("GITHUB_ACTIONS") or os.getenv("FORCE_COLOR") or os.getenv("PY_COLORS"):
        return True
    return None
