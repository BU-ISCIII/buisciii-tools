#!/usr/bin/env python

# Generic imports
import sys
import os
import logging

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


class Archive:
    def __init__(self, resolution_id=None, type=None, year=None, option=None):
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        if year is None:
            self.year = bu_isciii.utils.prompt_year()
        else:
            self.year = year

        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("archive")
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")
        # Obtain info from iskylims api
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )
        self.services_to_archive = rest_api.get_request(
            "services", "state", "delivered", "date", self.year
        )

        if type is None:
            self.option = bu_isciii.utils.prompt_selection(
                "Type",
                ["services_and_colaborations", "research"],
            )

        if option is None:
            self.option = bu_isciii.utils.prompt_selection(
                "Options",
                ["archive", "retrieve_from_archive"],
            )

    def archive(self):
        """
        Archive services in selected year
        """
        for service in self.services_to_archive:
            print(service["servicFolderName"])
            source = os.path.join(
                self.conf["data_path"],
                self.type,
                service["serviceUserId"]["Center"],
                service["serviceUserId"]["Area"],
                service["ServiceFolderName"],
            )
            dest = os.path.join(
                self.conf["archive_path"],
                self.type,
                service["serviceUserId"]["Center"],
                service["serviceUserId"]["Area"],
            )

            try:
                sysrsync.run(
                    source=self.source,
                    destination=self.destination,
                    options=data["options"],
                    sync_source_contents=False,
                )
                stderr.print(
                    "[green] Data copied to the sftp folder successfully",
                    highlight=False,
                )
            except OSError:
                stderr.print(
                    "[red] ERROR: Data could not be copied to the sftp folder.",
                    highlight=False,
                )
        return

    def retrieve_from_archive(self):
        """
        Copy a service back from archive
        """
        return

    def handle_archive(self):
        """
        Handle archive class options
        """
        if self.option == "archive":
            self.archive()
        if self.option == "retrieve_from_archive":
            self.retrieve_from_archive()
        return
