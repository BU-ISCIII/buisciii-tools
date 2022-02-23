#!/usr/bin/env python
"""
Common utility function for bu-isciii package.
"""
import logging
from logging.config import fileConfig
import os
import rich
import traceback
import questionary


def write_in_log(log_type, string_text, showing_traceback):
    """ Write actions in log"""

    def open_log(config_file):
        """ The function creates the log object to write logging information
        Input:
            config_file    # path of config file
        Return:
            logger
        """

        fileConfig(config_file)
        logger = logging.getLogger(__name__)
        return logger

    try:
        logger = logging.getLogger(__name__)
    except Exception:
        work_dir = os.getcwd()
        config_file = os.path.join(work_dir, "test")
        logger = open_log(config_file)
    if "error" in log_type:
        logger.error("-----------------    ERROR   ------------------")
        logger.error(string_text)
        if showing_traceback :
            logger.error("################################")
            logger.error(traceback.format_exc())
            logger.error("################################")
        logger.error("-----------------    END ERROR   --------------")
    else:
        logger.info(string_text)
    return


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
    resolution_id = questionary.text("Resolution id").ask()
    print(resolution_id)
    return resolution_id
