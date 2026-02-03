#!/usr/bin/env python

# import
import os
import re
import sys
import logging

import shutil
import rich

from datetime import datetime, timedelta

# local import
import buisciii
import buisciii.utils
import buisciii.config_json

log = logging.getLogger(__name__)

stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


# TODO: add to utils.py?
def timestamp_converter(timestamp):
    date_formated = datetime.fromtimestamp(timestamp)
    return date_formated


class LastModificationFinder:
    """
    Identifies the latest modification in a directory.
    """

    def __init__(self, path):
        self.path = path
        self.last_modified_time = 0

    def find_last_modification(self):
        """
        Return the latest modification datetime found in the directory tree.
        """
        self.get_last_modified(self.path)
        return timestamp_converter(self.last_modified_time)

    def get_last_modified(self, directory):
        """
        Update the latest modification timestamp for a directory.
        """
        last_modified_time = os.path.getmtime(directory)

        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                file_modified_time = os.path.getmtime(file_path)
                if file_modified_time > last_modified_time:
                    last_modified_time = file_modified_time

        if last_modified_time > self.last_modified_time:
            self.last_modified_time = last_modified_time


class AutoremoveSftpService:
    """
    Identifies services stored in an SFTP directory
    and removes those that have not been updated/modified
    within 14 days.
    """

    def __init__(self, path=None, days=14, conf=None):
        # Parse input path
        if path is None:
            use_default = buisciii.utils.prompt_yn_question(
                "Check default path (/data/ucct/bi/sftp/)?: ", dflt=False
            )
            if use_default:
                data_path = conf.get_configuration("global")["data_path"]
                self.path = os.path.join(data_path, "sftp")
            else:
                self.path = buisciii.utils.prompt_path(
                    msg="Directory where the SFTP site is allocated:"
                )
        else:
            self.path = path

        # Define the margin threshold of days to mark old services
        self.days = timedelta(days=days)
        stderr.print(
            "Services older than "
            + str(self.days.days)
            + " days will now be deleted from "
            + self.path
        )
        log.info(
            "Services older than "
            + str(self.days.days)
            + " days will now be deleted from "
            + self.path
        )

    # TODO: modify this. PR to make this method reusable outside the class
    def check_path_exists(self):
        """
        Verify that the SFTP base path exists.
        Exit the program if the path is not found.
        """
        if not os.path.exists(self.path):
            stderr.print(
                "[red]ERROR: The path: " + self.path + "does not exist. Exiting..."
            )
            log.error(f"ERROR: The path {self.path} does not exist. Exiting...")
            raise ValueError(f"The path {self.path} does not exist!")
        else:
            return True

    # Uses regex to identify sftp-services & gets their latest modification
    def get_sftp_services(self):
        """
        Scan the SFTP directory and collect services matching the expected
        naming pattern along with their last modification time.
        """
        self.sftp_services = {}  # {sftp-service_path : last_update}
        service_pattern = (
            r"^[SRV][A-Z]+[0-9]+_\d{8}_[A-Z0-9.-]+_[a-zA-Z]+(?:\.[a-zA-Z]+)?_[a-zA-Z]$"
        )
        stderr.print("[blue]Scanning " + self.path + "...")
        log.info(f"Scanning {self.path}...")
        for root, dirs, files in os.walk(self.path):
            for dir_name in dirs:
                match = re.match(service_pattern, dir_name)
                if match:
                    sftp_service_fullPath = os.path.join(root, dir_name)

                    # Get sftp-service last modification
                    service_finder = LastModificationFinder(sftp_service_fullPath)
                    service_last_modification = service_finder.find_last_modification()
                    self.sftp_services[sftp_service_fullPath] = (
                        service_last_modification
                    )
        if len(self.sftp_services) == 0:
            stderr.print(f"[yellow]No services found in {self.path}! Exiting...")
            log.warning(f"No services found in {self.path}! Exiting...")
            raise ValueError(f"No services found in {self.path}! Exiting...")

    def mark_toDelete(self):
        """
        Mark services whose last modification exceeds the allowed age threshold.
        """
        self.marked_services = []
        for key, value in self.sftp_services.items():
            if datetime.now() - value > self.days:
                self.marked_services.append(key)

    def remove_oldservice(self):
        """
        Remove all selected SFTP services after user confirmation.
        """
        if len(self.marked_services) == 0:
            stderr.print(
                "[yellow]SFTP up to date. There are no services older than "
                + str(self.days.days)
                + " days. Skipping..."
            )
            log.info(
                f"SFTP up to date! There are no services older than {str(self.days.days)} days. Exiting!"
            )
            sys.exit()
        else:
            service_elements = "\n".join(self.marked_services)
            stderr.print(
                "The following services will now be deleted from the SFTP:\n"
                + service_elements
            )
            log.info(
                "The following services will now be deleted from the SFTP:\n"
                + service_elements
            )
            confirm_sftp_delete = buisciii.utils.prompt_yn_question(
                "Are you sure? ", dflt=False
            )
            if confirm_sftp_delete:
                for service in self.marked_services:
                    try:
                        stderr.print("Deleting service: " + service)
                        log.info(f"Deleting service: {service}")
                        shutil.rmtree(service)
                    except OSError:
                        stderr.print(
                            "[red]ERROR: Cannot delete service folder:" + service
                        )
                        log.error("ERROR: Cannot delete service folder:" + service)
                        raise
            else:
                stderr.print("Aborting...")
                log.info("Aborting...")
                sys.exit()

    def handle_autoclean_sftp(self):
        """
        Execute the whole SFTP cleanup workflow.
        """
        self.check_path_exists()
        self.get_sftp_services()
        self.mark_toDelete()
        self.remove_oldservice()
