#!/usr/bin/env python

# Generic imports
import sys
import os
import logging
import filecmp # Not sure if generic

import sysrsync
import rich

# Local imports
import bu_isciii
import bu_isciii.utils
import bu_isciii.config_json
import bu_isciii.drylab_api

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)

# function to compare directories (archived and non-archived)
def dir_comparison(dir1, dir2):
    """
    Generates a filecmp.dircmp comparison object
    RECURSIVELY, checks each of the dirs to check if 
    they are the same.

    Heavily based on:
    https://stackoverflow.com/questions/4187564/recursively-compare-two-directories-to-ensure-they-have-the-same-files-and-subdi
    
    """
    comparison = filecmp.dircmp(dir1, dir2)
    if comparison.left_only or comparison.right_only or comparison.diff_files or comparison.funny_files:
        return False
    for subdir in comparison.common_dirs:
        if not dir_comparison(os.path.join(dir1, subdir), os.path.join(dir2,subdir)):
            return False
    return True

def get_service_paths(conf, type, service):
    """
    Given a service, a conf and a type, 
    get the path it would have in the 
    archive, and outside of it
    """

    # Path in archive
    archived = os.path.join(
        conf["archive_path"],
        type,
        service["serviceUserId"]["Center"],
        service["serviceUserId"]["Area"],
    )

    # Path out of archive
    non_archived = os.path.join(
        conf["data_path"],
        type,
        service["serviceUserId"]["Center"],
        service["serviceUserId"]["Area"],
    )

    return archived, non_archived

class Archive:
    """
    Class to perform the archivation and retrieval
    of a service
    """
    def __init__(self, resolution_id=None, type=None, year=None, option=None):
        
        # resolution_id = Nombre de la resolución
        # type = services_and_colaborations // research
        # year = año
        # option = archive/retrieve

        # assumption: year and no resolution_id >>> Batch management
        self.quantity = "Batch" if self.year is not None and self.resolution_id is None else None
        # assumption: resolution_id and no year >>> Single service management
        self.quantity = "Single service" if self.resolution_id is not None and self.year is None else None 

        if self.quantity is None:
            self.quantity = bu_isciii.utils.prompt_selection(
                "Working with a batch, or a single resolution?",
                ["Batch", "Single service"],
            )

        if self.quantity == "Batch" and self.year is None:
            self.year = bu_isciii.utils.prompt_year()

        elif self.quantity == "Single service" and self.resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()

        # Get configuration params from configuration.json
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("archive")

        # get data to connect to the api
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")
        
        # Obtain info from iskylims api with the conf_api info
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )
        self.services_to_move = rest_api.get_request(
            "services", "state", "delivered", "date", self.year
        )

        if type is None:
            self.type = bu_isciii.utils.prompt_selection(
                "Type",
                ["services_and_colaborations", "research"],
            )

        if option is None:
            self.option = bu_isciii.utils.prompt_selection(
                "Options",
                ["archive", "retrieve"],
            )

    def archive(self):
        """
        Archive services in selected year
        """
        for service in self.services_to_move:
            #stderr.print(service["servicFolderName"])

            dest, source = get_service_paths(self.conf, self.type, service)

            try:
                sysrsync.run(
                    source=source,
                    destination=dest,
                    options=self.conf["options"],
                    sync_source_contents=False,
                )
                stderr.print(
                    "[green] Data copied successfully to its destiny archive folder",
                    highlight=False,
                )
            except OSError as e:
                stderr.print(
                    "[red] ERROR: Data could not be copied to its destiny archive folder.",
                    highlight=False,
                )
                log.error(
                    f"Directory {self.source} could not be archived to {self.dest}.\
                        Reason: {e}"
                )
        return

    def retrieve_from_archive(self):
        """
        Copy a service back from archive
        """
        for service in self.services_to_move:
            #stderr.print(service["servicFolderName"])
            source = os.path.join(
                self.conf["archive_path"],
                self.type,
                service["serviceUserId"]["Center"],
                service["serviceUserId"]["Area"],
            )

            dest = os.path.join(
                self.conf["data_path"],
                self.type,
                service["serviceUserId"]["Center"],
                service["serviceUserId"]["Area"],
            )

            try:
                sysrsync.run(
                    source=source,
                    destination=dest,
                    options=self.conf["options"],
                    sync_source_contents=False,
                )
                stderr.print(
                    "[green] Data retrieved successfully from its archive folder.",
                    highlight=False,
                )
            except OSError as e:
                stderr.print(
                    "[red] ERROR: Data could not be retrieved from its archive folder.",
                    highlight=False,
                )
                log.error(
                    f"Directory {self.source} could not be archived to {self.dest}.\
                        Reason: {e}"
                )
        
        return

    def delete_origin(self):
        """
        Delete the origin of the previous archive or retrieval
        """
        for service in self.services_to_move:
            if self.option == "archive":
                dest, source = get_service_paths(self.conf, self.type, service)
            elif self.option == "retrieve":
               source, dest = get_service_paths(self.conf, self.type, service)

            if not dir_comparison(source, dest):

            
        return

    def handle_archive(self):
        """
        Handle archive class options
        """
        if self.option == "archive":
            self.archive()
        if self.option == "retrieve":
            self.retrieve_from_archive()
        return