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


class LastMofdificationFinder:
    """
    Identifies the lates modification in a directory
    """

    def __init__(self, path):
        self.path = path
        self.last_modified_time = 0

    def find_last_modification(self):
        self.get_last_modified(self.path)
        return timestamp_converter(self.last_modified_time)

    def get_last_modified(self, directory):
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
    Identifies service's stored in an sftp directory
    and remove those that have not been updated/modified
    within 14 days
    """

    def __init__(self, path=None, days=14, conf=None):
        # Parse input path
        if path is None:
            use_default = buisciii.utils.prompt_yn_question(
                "Use default path?: ", dflt=False
            )
            if use_default:
                data_path = conf.get_configuration("global")["data_path"]
                self.path = os.path.join(data_path, "sftp")
            else:
                self.path = buisciii.utils.prompt_path(
                    msg="Directory where the sftp site is allocated:"
                )
        else:
            self.path = path

        # Define the margin threshold of days to mark old services
        self.days = timedelta(days=days)
        stderr.print(
            "Services older than "
            + str(self.days.days)
            + " days are going to be deleted from "
            + self.path
        )

    # TODO: modify this. PR to make this method reusable outside the class
    def check_path_exists(self):
        # if the folder path is not found, then bye
        if not os.path.exists(self.path):
            stderr.print(
                "[red]ERROR: It seems like finding the correct path is beneath me. I apologise. The path:"
                + self.path
                + "does not exitst. Exiting.." % self.path
            )
            sys.exit()
        else:
            return True

    # Uses regex to identify sftp-services & gets their lates modification
    def get_sftp_services(self):
        self.sftp_services = {}  # {sftp-service_path : last_update}
        service_pattern = (
            r"^[SRV][A-Z]+[0-9]+_\d{8}_[A-Z0-9.-]+_[a-zA-Z]+(?:\.[a-zA-Z]+)?_[a-zA-Z]$"
        )

        stderr.print("[blue]Scanning " + self.path + "...")
        for root, dirs, files in os.walk(self.path):
            for dir_name in dirs:
                match = re.match(service_pattern, dir_name)
                if match:
                    sftp_service_fullPath = os.path.join(root, dir_name)

                    # Get sftp-service last modification
                    service_finder = LastMofdificationFinder(sftp_service_fullPath)
                    service_last_modification = service_finder.find_last_modification()
                    self.sftp_services[sftp_service_fullPath] = (
                        service_last_modification
                    )
        if len(self.sftp_services) == 0:
            sys.exit(f"No services found in {self.path}")

    # Mark services older than $days
    def mark_toDelete(self):
        self.marked_services = []

        for key, value in self.sftp_services.items():
            if datetime.now() - value > self.days:
                self.marked_services.append(key)

    # Delete marked services
    def remove_oldservice(self):
        if len(self.marked_services) == 0:
            stderr.print(
                "[yellow]sftp-site up to date. There are no services  older than "
                + str(self.days.days)
                + " days. Skiping autoclean-sftp... "
            )
            sys.exit()
        else:
            service_elements = "\n".join(self.marked_services)
            stderr.print(
                "The following services are going to be deleted from the sftp:\n"
                + service_elements
            )
            confirm_sftp_delete = buisciii.utils.prompt_yn_question(
                "Are you sure?: ", dflt=False
            )
            if confirm_sftp_delete:
                for service in self.marked_services:
                    try:
                        stderr.print("Deleting service: " + service)
                        shutil.rmtree(service)

                    except OSError:
                        stderr.print(
                            "[red]ERROR: Cannot delete service folder:" + service
                        )
            else:
                stderr.print("Aborting ...")
                sys.exit()

    def handle_autoclean_sftp(self):
        self.check_path_exists()
        self.get_sftp_services()
        self.mark_toDelete()
        self.remove_oldservice()
