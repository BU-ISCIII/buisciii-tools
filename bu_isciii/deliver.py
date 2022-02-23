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
from bdb import set_trace
from distutils.log import info
import json
import sys
from warnings import catch_warnings
import sysrsync


import argparse

# import requests

from drylab_api import RestServiceApi

class Deliver:
    def __init__(
        self,
        source=,
        destination=,
        service_number =,
        
    ):
    

        rest_api = RestServiceApi("http://iskylims.isciiides.es/", "drylab/api/")
        services_queue = rest_api.get_request("serviceFullData", "service", "SRVCNM160")

    def copy_sftp:

        path = open("schemas/schema_sftp_copy.json")
        data = json.load(path)

        try:
            sysrsync.run(
            source=source,
            destination=destination,
            options=data["options"],
            exclusions=data["exclusions"],
            sync_source_contents=False,   
            )
            message = "Correct rsync"
        except:
            message = "Error rsync" 
        return message
    
    def create_report:

        info =[
            
        SERVICE_ID = services_queue["Resolutions"]["resolutionFullNumber"],
        SERVICE_NUMBER = services_queue["Service"]["serviceRequestNumber"],
        RESOLUTION_NUMBER = services_queue["Resolutions"]["resolutionNumber"]
        SERVICE_REQUEST_DATE = services_queue["Service"]["serviceCreatedOnDate"]
        SERVICE_RESOLUTION_DATE = services_queue["Resolutions"]["resolutionDate"]
        SERVICE_IN_PROGRESS_DATE = services_queue["Resolutions"]["resolutionOnInProgressDate"]

        ]
        



        

            """
            
            SERVICE.IN_PROGRESS_DATE  - resolutionOnInProgressDate
            SERVICE.ESTIMATED_DELIVERY_DATE - resolutionEstimatedDate
            SERVICE.DELIVERY_DATE - resolutionDeliveryDate
            SERVICE.SERVICE_NOTES - - serviceUserId.first_name
            USER.LAST_NAME - serviceUserId.last_name
            USER.EMAIL - serviceUserId.email
            SERVICE.SEQUENCING_CENTER - serviceSeqCenter
            RUN_NAME - runName
            PROJECTS - ¿lista de projects name?
            PROJECT_NAME - projectName
            SAMPLES - sampleName
            """
