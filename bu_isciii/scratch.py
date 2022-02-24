#!/usr/bin/env python
"""
=============================================================
HEADER
=============================================================
INSTITUTION: BU-ISCIII
AUTHOR: Sara Monzon; Sarai Varona
MAIL: smonzon@isciii.es; s.varona@isciii.es
CREATED: 24-02-2022
DESCRIPTION:
OPTIONS:

USAGE:

REQUIREMENTS:

TO DO:
================================================================
END_OF_HEADER
================================================================
"""
# Generic imports
# import sys
# import os
import logging

#import shutil
import rich

# Local imports
import bu_isciii
import bu_isciii.utils
from bu_isciii.service_json import ServiceJson
from bu_isciii.drylab_api import RestServiceApi

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)

class Scratch:
    def __init__(
        self,
        resolution_id=None,
        source=None,
        destination=None,
    ):
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

        rest_api = RestServiceApi("http://iskylims.isciiides.es/", "drylab/api/")
        self.resolution_info = rest_api.get_request(
            "resolution", "resolution", self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutionFullNumber"]

    def copy_scratch(self):
        stderr.print(
            "[blue]I will copy the service folder for %s to scratch!" % self.resolution_id
        )
