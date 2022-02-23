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
import json

# import sys
import os

# import argparse
# from warnings import catch_warnings
from distutils.log import info
import logging

import sysrsync
import rich

# import requests
import bu_isciii
import bu_isciii.utils
from bu_isciii.drylab_api import RestServiceApi

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)


class Deliver:
    def __init__(
        self,
        resolution_id=None,
        source=None,
        destination=None,
    ):

        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
            print(self.resolution_id)
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
        self.services_queue = rest_api.get_request(
            "serviceFullData", "service", self.resolution_id
        )

    def copy_sftp(self):

        path = open(
            os.path.join(
                os.path.dirname("__file__"), "schemas", "schema_sftp_copy.json"
            )
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
        except Exception:
            stderr.print(
                "[red] ERROR: Data could not be copied to the sftp folder.",
                highlight=False,
            )

    def create_report(self):

        info = {
            "SERVICE_ID": self.services_queue["Resolutions"]["resolutionFullNumber"],
            "SERVICE_NUMBER": self.services_queue["Service"]["serviceRequestNumber"],
            "RESOLUTION_ID": self.services_queue["Resolutions"]["resolutionNumber"],
            "SERVICE_REQUEST_DATE": self.services_queue["Service"][
                "serviceCreatedOnDate"
            ],
            "SERVICE_RESOLUTION_DATE": self.services_queue["Resolutions"][
                "resolutionDate"
            ],
            "SERVICE_IN_PROGRESS_DATE": self.services_queue["Resolutions"][
                "resolutionOnInProgressDate"
            ],
            "SERVICE_ESTIMATED_DELIVERY_DATE": self.services_queue["Resolutions"][
                "resolutionEstimatedDate"
            ],
            "SERVICE_DELIVERY_DATE": self.services_queue["Resolutions"][
                "resolutionDeliveryDate"
            ],
            "SERVICE_NOTES": self.services_queue["Service"]["serviceUserId"][
                "first_name"
            ],
            "USER_LAST_NAME": self.services_queue["Service"]["serviceUserId"][
                "last_name"
            ],
            "USER_EMAIL": self.services_queue["Service"]["serviceUserId"]["email"],
            "SERVICE_SEQUENCING_CENTER": self.services_queue["Service"][
                "serviceSeqCenter"
            ],
            # RUN_NAME,
            # PROJECTS,
            # SAMPLES ,
            "PROJECT_NAME": self.services_queue["Sample"]["sampleName"],
        }
        print(info)

        """
        RUN_NAME - runName
        PROJECTS - ¿lista de projects name?
        PROJECT_NAME - projectName
        SAMPLES - sampleName
        """
