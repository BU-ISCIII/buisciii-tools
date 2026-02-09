#!/usr/bin/env python

# Generic imports
import os
import logging
from rich.console import Console
import sysrsync
from sysrsync.exceptions import RsyncError
from datetime import datetime

# Local imports
import buisciii
import buisciii.utils
import buisciii.drylab_api
import buisciii.service_json

log = logging.getLogger(__name__)

stderr = Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


class CopySftp:
    def __init__(
        self,
        resolution_id=None,
        path=None,
        ask_path=False,
        sftp_folder=None,
        api_user=None,
        api_password=None,
        conf=None,
    ):
        if resolution_id is None:
            self.resolution_id = buisciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        # Load conf
        self.conf = conf.get_configuration("sftp_copy")
        conf_api = conf.get_configuration("xtutatis_api_settings")

        # Obtain info from iSkyLIMS API
        rest_api = buisciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"], api_user, api_password
        )

        self.resolution_info = rest_api.get_request(
            request_info="service-data", safe=True, resolution=self.resolution_id
        )
        if sftp_folder is None:
            self.sftp_folder = buisciii.utils.get_sftp_folder(
                conf, self.resolution_info
            )[0]
        else:
            self.sftp_folder = sftp_folder

        self.service_folder = self.resolution_info["resolutions"][0][
            "resolution_full_number"
        ]
        self.services_requested = self.resolution_info["resolutions"][0][
            "available_services"
        ]
        self.sftp_options = conf.get_find("sftp_copy", "options")
        self.services_to_copy = buisciii.utils.get_service_ids(self.services_requested)

        self.last_folders = self.get_last_folders(
            self.services_to_copy, type="last_folder"
        )
        if ask_path and path is None:
            stderr.print("Directory where you want to create the service folder.")
            self.path = buisciii.utils.prompt_path(msg="Path")
        elif path == "-a":
            stderr.print(
                "[red]ERROR: Either give a path or make the terminal ask you for a path, not both."
            )
            log.error(
                "ERROR: Either give a path or make the terminal ask you for a path, not both."
            )
            raise ValueError(
                "Either give a path or make the terminal ask you for a path, not both."
            )
        elif path is not None and ask_path is False:
            self.path = path
        elif path is not None and ask_path is not False:
            stderr.print(
                "[red]ERROR: Either give a path or make the terminal ask you a path, not both."
            )
            log.error(
                "ERROR: Either give a path or make the terminal ask you a path, not both."
            )
            raise ValueError(
                "Either give a path or make the terminal ask you for a path, not both."
            )
        else:
            self.path = buisciii.utils.get_service_paths(
                conf,
                "services_and_colaborations",
                self.resolution_info,
                "non_archived_path",
            )

        self.full_path = os.path.join(self.path, self.service_folder)

    def get_last_folders(self, services_ids, type="last_folder"):
        """
        Description:
            Get last folders from service conf.

        Usage:
            object.get_last_folders(services_ids, type = "last_folder")

        Params:
            services_ids [list]: list with services IDs selected.
            type [string]: "last_folder" for getting the param from service.json.
        """
        service_conf = buisciii.service_json.ServiceJson()
        last_folders_list = []
        for service in services_ids:
            try:
                item = service_conf.get_find_deep(service, type)
                if item not in last_folders_list:
                    last_folders_list.append(item)
            except KeyError:
                stderr.print(
                    "[red]ERROR: Service ID %s not found in the services.json file."
                    % service
                )
                log.error(
                    f"ERROR: Service ID {service} not found in the services.json file."
                )
                raise

        return last_folders_list

    def listdirs(self, final_path):
        """
        Description:
            Print all files contained within a given directory and its subdirectories.
        """
        for path, subdirs, files in os.walk(final_path):
            for name in files:
                print(os.path.join(path, name))

    def copy_sftp(self):
        """
        Description:
            Copy the service folder to the configured SFTP destination using rsync.
        """
        if self.service_folder in self.full_path:
            today_date = datetime.today().strftime("%Y%m%d")
            log_command = (
                "--log-file=" + self.full_path + "/DOC/rsync_" + today_date + ".log"
            )
            self.sftp_options.append(log_command)
            stderr.print(
                f"[yellow]The service folder will now be copied to the '{self.sftp_folder}' SFTP folder."
            )
            log.info(
                f"The service folder will be copied to the '{self.sftp_folder}' SFTP folder."
            )
            try:
                if self.conf["protocol"] == "rsync":
                    sysrsync.run(
                        source=self.full_path,
                        destination=self.sftp_folder,
                        options=self.sftp_options,
                        exclusions=self.conf["exclusions"],
                        sync_source_contents=False,
                    )
                    stderr.print(
                        "[green]Data copied to the SFTP folder successfully!",
                        highlight=False,
                    )
                    log.info("Data copied to the SFTP folder successfully!")
                else:
                    stderr.print(
                        "[red]This protocol is not allowed at the moment",
                        highlight=False,
                    )
                    log.error("This protocol is not allowed at the moment!")
                    raise NotImplementedError(
                        "This protocol is not allowed at the moment!"
                    )
            except RsyncError:
                stderr.print(
                    "[yellow]Data copied to the SFTP with errors.",
                    highlight=False,
                )
                log.warning("Data copied to the SFTP with errors.")
                raise
            finally:
                for folders_list in self.last_folders:
                    final_folder = os.path.join(
                        self.sftp_folder, self.service_folder, folders_list
                    )
                    stderr.print(
                        "Listing the content of the final folder %s:" % folders_list
                    )
                    self.listdirs(final_folder)
        else:
            stderr.print(
                "[red]ERROR: Service number %s not in the source path %s"
                % (self.service_folder, self.full_path)
            )
            log.error(
                f"ERROR: Service number {self.service_folder} not in the source path {self.full_path}"
            )
            raise ValueError(
                f"ERROR: Service number {self.service_folder} not in the source path {self.full_path}"
            )
        return True
