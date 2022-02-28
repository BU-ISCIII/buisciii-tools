#!/usr/bin/env python
from datetime import datetime
import logging
import rich.console
import os
import sys

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


class BioinfoDoc:
    def __init__(
        self,
        resolution_id=None,
        local_folder=None,
        type=None,
    ):
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id
        if local_folder is None:
            self.local_folder = bu_isciii.utils.prompt_path(
                msg="Path where bioinfo folder is mounted"
            )
        else:
            self.local_folder = local_folder
        if not os.path.exists(self.local_folder):
            stderr.print("[red] Folder does not exist. " + self.local_folder + "!")
            sys.exit(1)
        if type is None:
            self.type = bu_isciii.utils.prompt_selection(
                msg="Select the documentation type you want to create",
                choices=["request", "resolution", "delivery"],
            )

        conf_doc = bu_isciii.config_json.ConfigJson().get_configuration("bioinfo_doc")
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )
        resolution_info = rest_api.get_request(
            "resolutionFullData", "resolution", self.resolution_id
        )
        if not resolution_info:
            stderr.print(
                "[red] Unable to fetch information for resolution "
                + self.resolution_id
                + "!"
            )
            sys.exit(1)
        resolution_folder = resolution_info["Resolutions"]["resolutionFullNumber"]
        # if "YEAR" in conf_doc["root_folder"]:
        #     year_position = conf_doc["root_folder"].index("YEAR")
        #     conf_doc["root_folder"][year_position] = str(datetime.now().year)
        year = str(datetime.now().year)
        self.service_folder = os.path.join(
            self.local_folder, conf_doc["services_path"], year, resolution_folder
        )
        self.folders = conf_doc["service_folder"]
        self.resolution_id = resolution_info["Resolutions"]["resolutionNumber"]

    def create_structure(self):
        if os.path.exists(self.service_folder):
            if bu_isciii.utils.prompt_skip_folder_creation():
                return
        stderr.print(
            "[blue] Creating the resolution folder for " + self.resolution_id + "!"
        )
        log.info("Creating service folder for %s", self.resolution_id)
        if not os.path.exists(self.service_folder):
            for folder in self.folders:
                os.makedirs(os.path.join(self.service_folder, folder), exist_ok=True)
            log.info("Service folders created")
        return

    def create_request_documentation(self):
        return
