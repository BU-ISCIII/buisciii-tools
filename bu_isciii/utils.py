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


def prompt_service_dir_path():
    stderr.print("Service path to copy to execution temporal directory")
    source = questionary.path("Source path").unsafe_ask()
    return source


def prompt_tmp_dir_path():
    stderr.print("Temporal directory destination to execute sercive")
    source = questionary.path("Source path").unsafe_ask()
    return source


def prompt_source_path():
    stderr.print("Directory containing files cd to transfer")
    source = questionary.path("Source path").unsafe_ask()
    return source


def prompt_destination_path():
    stderr.print("Directory to which the files will be transfered")
    destination = questionary.path("Destination path").unsafe_ask()
    return destination


def prompt_service_selection(choices):
    stderr.print("Which selected service do you want to copy the template for?")
    selection = questionary.select("Service label:", choices=choices).unsafe_ask()
    return selection


def prompt_path():
    stderr.print("Directory where you want to create the service folder.")
    source = questionary.path("Path").unsafe_ask()
    return source


def prompt_skip_folder_creation():
    stderr.print("Do you want to skip folder creation? (Y/N)")
    confirmation = questionary.confirm("Skip?").unsafe_ask()
    return confirmation


def prompt_direction_scratch(choices):
    stderr.print("In which direction do you want to execute the rsync command?")
    selection = questionary.select("Directions:", choices=choices).unsafe_ask()
    return selection
