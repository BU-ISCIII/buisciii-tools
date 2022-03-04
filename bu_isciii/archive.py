#!/usr/bin/env python

# Generic imports
import sys
import os
import logging

import shutil
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
    def __init__(
        self, resolution_id=None, type=None, year=None
    ):
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        self.path = bu_isciii.config_json.ConfigJson().get_configuration("archive")["archived_path"]
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")
        # Obtain info from iskylims api
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )
        self.resolution_info = rest_api.get_request(
            "services", "resolution", self.resolution_id
        )
