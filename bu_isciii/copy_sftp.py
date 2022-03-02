"""
 =============================================================
 HEADER
 =============================================================
 INSTITUTION: BU-ISCIII
 AUTHOR: Erika Kvalem Soto
 ================================================================
 END_OF_HEADER
 ================================================================

 """
# from cgitb import html
import json

# import jinja2
# import markdown


# import sys
import os

# import argparse
# from warnings import catch_warnings
# from distutils.log import info
import logging

# from numpy import True

import sysrsync
import rich

# import requests
import bu_isciii
import bu_isciii.utils

# from bu_isciii.drylab_api import RestServiceApi
import bu_isciii.drylab_api

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)


class CopySftp:
    def __init__(
        self,
        source=None,
        destination=None,
    ):
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

    def copy_sftp(self):
        path = open(
            os.path.join(os.path.dirname(__file__), "schemas", "schema_sftp_copy.json")
        )
        data = json.load(path)

        try:
            sysrsync.run(
                source=self.source,
                destination=self.destination,
                options=data["options"],
                exclusions=data["exclusions"],
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
        return True
