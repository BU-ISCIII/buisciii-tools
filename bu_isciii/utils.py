#!/usr/bin/env python
"""
Common utility function for bu-isciii package.
"""

import os
import questionary

def rich_force_colors():
    """
    Check if any environment variables are set to force Rich to use coloured output
    """
    if os.getenv("GITHUB_ACTIONS") or os.getenv("FORCE_COLOR") or os.getenv("PY_COLORS"):
        return True
    return None

def prompt_resolution_id():
    stderr.print("Specify the name resolution id for the service you want to create. You can obtain this from iSkyLIMS. eg. SRVCNM584.1")
    questionary.text("Resolution id").ask()
