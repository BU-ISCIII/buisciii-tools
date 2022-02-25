#!/usr/bin/env python
"""
Common utility function for bu-isciii package.
"""
import os
import rich
import questionary


def rich_force_colors():
    """
    Check if any environment variables are set to force Rich to use coloured output
    """
    if (
        os.getenv("GITHUB_ACTIONS")
        or os.getenv("FORCE_COLOR")
        or os.getenv("PY_COLORS")
    ):
        return True
    return None


stderr = rich.console.Console(
    stderr=True, style="dim", highlight=False, force_terminal=rich_force_colors()
)


def prompt_resolution_id():
    stderr.print(
        "Specify the name resolution id for the service you want to create. You can obtain this from iSkyLIMS. eg. SRVCNM584.1"
    )
    resolution_id = questionary.text("Resolution id").unsafe_ask()
    return resolution_id


def prompt_source_path():
    stderr.print("Directory containing files cd to transfer")
    source = questionary.path("Source path").unsafe_ask()
    return source


def prompt_destination_path():
    stderr.print("Directory to which the files will be transfered")
    destination = questionary.path("Destination path").unsafe_ask()
    return destination


def prompt_selection(msg, choices):
    selection = questionary.select(msg, choices=choices).unsafe_ask()
    return selection


def prompt_path():
    stderr.print("Directory where you want to create the service folder.")
    source = questionary.path("Path").unsafe_ask()
    return source

def prompt_yn_question(msg):
    confirmation = questionary.confirm(msg).unsafe_ask()
    return confirmation

def prompt_skip_folder_creation():
    stderr.print("Do you want to skip folder creation? (Y/N)")
    confirmation = questionary.confirm("Skip?").unsafe_ask()
    return confirmation
