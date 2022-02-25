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
import jinja2


# import sys
import os

# import argparse
# from warnings import catch_warnings
# from distutils.log import info
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

    def create_report(self):

        values_view = self.services_queue.values()
        value_iterator = iter(values_view)

        service = next(value_iterator)
        resolution = next(value_iterator)
        samples = next(value_iterator)

        service_id = resolution["resolutionFullNumber"]
        service_number = service["serviceRequestNumber"]
        resolution_id = resolution["resolutionNumber"]

        try:
            service_request_date = service["serviceCreatedOnDate"]
        except service_request_date.HTTPError:
            print("Resolution date is not defined")
        try:
            service_resolution_date = resolution["resolutionDate"]
        except service_resolution_date.HTTPError:
            print("Resolution date is not defined")
        try:
            service_in_progress_date = resolution["resolutionOnInProgressDate"]
        except service_in_progress_date.HTTPError:
            print("In pogress date is not defined")
        try:
            service_estimated_delivery_date = resolution["resolutionEstimatedDate"]
        except service_estimated_delivery_date.HTTPError:
            print("Estimated delivery date is not defined")
        try:
            service_delivery_date = resolution["resolutionDeliveryDate"]
        except service_delivery_date.HTTPError:
            print("Delivery date is not defined! Make the resolution!")

        service_notes = service["serviceNotes"]
        service_notes = service_notes.replace("\r", "")
        service_notes = service_notes.replace("\n", " ")
        username = service["serviceUserId"]["username"]
        user_first_name = service["serviceUserId"]["first_name"]
        user_last_name = service["serviceUserId"]["last_name"]
        user_email = service["serviceUserId"]["email"]
        service_sequencing_center = service["serviceSeqCenter"]
        run_name = [x["runName"] for x in samples]
        projects = [x["projectName"] for x in samples]
        run_name = list(dict.fromkeys(run_name))
        projects = list(dict.fromkeys(projects))
        samples = [x["sampleName"] for x in samples]

        json_data = {
            "id": service_id,
            "service_number": service_number,
            "resolution_number": resolution_id,
            "service_request_date": service_request_date,
            "service_resolution_date": service_resolution_date,
            "service_in_progress_date": service_in_progress_date,
            "service_estimated_delivery_date": service_estimated_delivery_date,
            "service_delivery_date": service_delivery_date,
            "service_notes": service_notes,
            "user_first_name": user_first_name,
            "user_last_name": user_last_name,
            "username": username,
            "user_email": user_email,
            "service_sequencing_center": service_sequencing_center,
            "run_name": run_name,
        }

        TEMPLATE_FILE = "templates/jinja_template.j2"
        BASEPATH = os.path.dirname(os.path.realpath(__file__))
        templateLoader = jinja2.FileSystemLoader(searchpath=BASEPATH)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(TEMPLATE_FILE)

        # Create markdown
        outputText = template.render(json_data)
        file = open("INFRES_" + json_data["service_number"] + ".md", "wb")
        file.write(outputText.encode("utf-8"))
        file.close()
