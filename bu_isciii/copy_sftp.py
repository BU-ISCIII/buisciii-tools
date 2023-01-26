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
    def __init__(self, resolution_id=None, path=None, ask_path=False, sftp_folder=None):

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

        if sftp_folder is None:
            self.sftp_folder = bu_isciii.utils.prompt_destination_path()
        else:
            self.sftp_folder = sftp_folder

        # Load conf
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("sftp_copy")
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")

        # Obtain info from iskylims api
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )

        self.resolution_info = rest_api.get_request(
            "serviceFullData", "resolution", self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutions"][0][
            "resolutionFullNumber"
        ]
        self.services_requested = self.resolution_info["resolutions"][0][
            "availableServices"
        ]
        self.sftp_options = bu_isciii.config_json.ConfigJson().get_find(
            "sftp_copy", "options"
        )
        self.sftp_exclusions = bu_isciii.config_json.ConfigJson().get_find(
            "sftp_copy", "exclusions"
        )
        self.services_to_copy = bu_isciii.utils.get_service_ids(self.services_requested)

        self.last_folders = self.get_last_folders(
            self.services_to_copy, type="last_folder"
        )
        if ask_path and path is None:
            stderr.print("Directory where you want to create the service folder.")
            self.path = bu_isciii.utils.prompt_path(msg="Path")
        elif path == "-a":
            stderr.print(
                "[red] ERROR: Either give a path or make the terminal ask you a path, not both."
            )
            sys.exit()
        elif path is not None and ask_path is False:
            self.path = path
        elif path is not None and ask_path is not False:
            stderr.print(
                "[red] ERROR: Either give a path or make the terminal ask you a path, not both."
            )
            sys.exit()
        else:
            self.path = self.get_service_paths(self.conf)

        self.full_path = os.path.join(self.path, self.service_folder)

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
                    % service
                )
                stderr.print("traceback error %s" % e)
                sys.exit()

        return last_folders_list

    def get_service_paths(self, conf):
        """
        Given a service, a conf and a type,
        get the path it would have service
        """
        service_path = os.path.join(
            conf["data_path"],
            "services_and_colaborations",
            self.resolution_info["serviceUserId"]["profile"]["profileCenter"],
            self.resolution_info["serviceUserId"]["profile"][
                "profileClassificationArea"
            ].lower(),
        )
        return service_path

    def listdirs(self, final_path):
        for path, subdirs, files in os.walk(final_path):
            for name in files:
                print(os.path.join(path, name))

    def copy_sftp(self):
        if self.service_folder in self.full_path:
            today_date = datetime.today().strftime("%Y%m%d")
            log_command = (
                "--log-file=" + self.full_path + "/DOC/rsync_" + today_date + ".log"
            )
            self.sftp_options.append(log_command)
            try:
                sysrsync.run(
                    source=self.full_path,
                    destination=self.sftp_folder,
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
                    final_folder = os.path.join(
                        self.sftp_folder, self.service_folder, folders_list
                    )
                    stderr.print(
                        "Listing the content of the final folder %s" % folders_list
                    )
                    self.listdirs(final_folder)
        else:
            stderr.print(
                "[red]ERROR: Service number %s not in the source path %s"
                % (self.service_folder, self.full_path)
            )
            sys.exit()
        return True
