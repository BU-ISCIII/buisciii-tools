#!/usr/bin/env python

"""
 =============================================================
 HEADER
 =============================================================
 INSTITUTION: BU-ISCIII
 AUTHORS: Erika Kvalem Soto and Sarai Varona Fernandez
 ================================================================
 END_OF_HEADER
 ================================================================

 """

# Generic imports
import os
import sys
import logging
from rich.console import Console
import json
import sysrsync
from sysrsync.exceptions import RsyncError
from datetime import datetime

# Local imports
import bu_isciii
import bu_isciii.utils
import bu_isciii.drylab_api
import bu_isciii.service_json

log = logging.getLogger(__name__)
stderr = Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)

class CopySftp:
    def __init__(self, resolution_id=None, source=None, destination=None):

        """
        Description:
            Class to perform the copy of the service to sftp folfer.

        Usage:

        Attributes:

        Methods:

        """

        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        if source is None:
            self.source = bu_isciii.utils.prompt_source_path()
        else:
            self.source = source

        if destination is None:
            self.destination = bu_isciii.utils.prompt_destination_path()
        else:
            self.destination = destination

        # Load conf
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("sftp_copy")
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")

        # Obtain info from iskylims api
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )

        self.resolution_info = rest_api.get_request(
            "resolutionFullData", "resolution", self.resolution_id
        )
        self.service_folder = self.resolution_info["Resolutions"][
            "resolutionFullNumber"
        ]
        self.services_requested = self.resolution_info["Resolutions"][
            "availableServices"
        ]
        self.sftp_options = bu_isciii.config_json.ConfigJson().get_find(
            "sftp_copy", "options"
        )

        self.sftp_exclusions = bu_isciii.config_json.ConfigJson().get_find(
            "sftp_copy", "exclusions"
        )
        self.services_to_copy = bu_isciii.utils.get_service_ids(
            self.services_requested
        )

        self.last_folders = self.get_last_folders(self.services_to_copy, type="last_folder")

    def get_last_folders(self, services_ids, type="last_folder"):
        """
        Description:
            Get last folders from service conf

        Usage:
            object.get_last_folders(services_ids, type = "last_folder")

        Params:
            services_ids [list]: list with services ids selected.
            type [string]: "last_folder" for getting the param from service.json
        """
        service_conf = bu_isciii.service_json.ServiceJson()
        last_folders_list = []
        for service in services_ids:
            try:
                items = service_conf.get_find_deep(service, type)
                last_folders_list.append(items)
            except KeyError as e:
                stderr.print(
                    "[red]ERROR: Service id %s not found in services json file."
                    % services_ids[0]
                )
                stderr.print("traceback error %s" % e)
                sys.exit()

        return last_folders_list

    def copy_sftp(self):
         if self.service_folder in self.source:
             today_date = datetime.today().strftime("%Y%m%d")
             log_command = "--log-file="+self.source + '/DOC/rsync_' + today_date + '.log'
             self.sftp_options.append(log_command)
             try:
                log = sysrsync.run(
                    source=self.source,
                    destination=self.destination,
                    options=self.sftp_options,
                    exclusions=self.sftp_exclusions,
                    sync_source_contents=False,
                )
                stderr.print(
                    "[green] Data copied to the sftp folder successfully",
                    highlight=False,
                )
             except RsyncError as e:
                stderr.print(e)
                stderr.print(
                    "[yellow] Data copied to the sftp with errors.",
                    highlight=False,
                )
             finally:
                 for folders_list in self.last_folders:
                     final_folder = os.path.join(self.destination, self.service_folder, folders_list)
                     stderr.print("Listing the content of the final folder %s" % folders_list)
                     print(os.system("ls "+final_folder))
         else:
             stderr.print(
             "[red]ERROR: Service number %s not in the source path %s"
             % (self.service_folder, self.source)
             )
             sys.exit()
         return True
