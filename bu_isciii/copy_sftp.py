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


# Deliver automatization
# Copy in sftp

from bdb import set_trace
import json
import sys
import sysrsync

import argparse

# import requests


from drylab_api import RestServiceApi


def parser_args(args=None):
    Description = "Copy resolution FOLDER to sftp"
    Epilog = """Example usage: python copy_sftp.py --source /home/erika.kvalem/Documents/BU_ISCIII/pruebas_source/ --destination /home/erika.kvalem/Documents/BU_ISCIII/prubas_destination --options -r --exclusions "*_NC" --service_number SRVIIER080"""

    parser = argparse.ArgumentParser(description=Description, epilog=Epilog)
    parser.add_argument(
        "-s", "--source", type=str, help="Directory containing files cd to transfer"
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=str,
        help="Directory to which the files will be transfered",
    )
    parser.add_argument(
        "--sn",
        "--service_number",
        type=str,
        help="Service Number",
    )
    parser.add_argument(
        "--p",
        "--protocol",
        type=str,
        required=False,
        default=None,
        help="command to execute",
    )
    parser.add_argument(
        "--o",
        "--options",
        type=str,
        required=False,
        default=None,
        help="command parameters",
    )
    parser.add_argument(
        "--e",
        "--exclusions",
        required=False,
        default=None,
        type=str,
        help="Excluded files in the source folder that will not be transfered",
    )
    return parser.parse_args(args)


path = open("schemas/schema_sftp_copy.json")
data = json.load(path)


def main(args=None):
    args = parser_args(args)

    """
    sysrsync.run(
        source=args.source,
        destination=args.destination,
        options=data["options"],
        exclusions=data["exclusions"],
        sync_source_contents=False,
    )
    """

    # Change status in iskylims
    rest_api = RestServiceApi("http://iskylims.isciiides.es/", "drylab/api/")
    services_queue = rest_api.get_request("serviceFullData", "service", "SRVIIER080")
    print(services_queue.items())
    # keys_list = list(services_queue)
    # for i in services_queue:
    #    print(i, services_queue[i])
    # key = keys_list[0]
    # print(key)

    # services_queue = rest_api.get_request("serviceFullData", "services", "SRVIIER080")
    # rest_api.get_request("services", "state", "queued")
    # print(services_queue)


# services_queue = rest_api.put_request("resolution/", "state", "Delivery")

# services_queue = rest_api.get_request("serviceFullData", "service", "SRVCNM572_20220209_SARSCOV278_icasas_S/")


# def put_request(self, request_info, parameter, value):

"""
Request:    'drylab/api/serviceFullData?services=<service_nuber>'
    Method:     get
    Description:    return the Samples, resolutions, and the information requested
            when creating the service with the following information:
            Related to service:
                'pk', 'serviceRequestNumber','serviceStatus', 'serviceUserId',
                'serviceCreatedOnDate', 'serviceSeqCenter', 'serviceAvailableService',
                'serviceFileExt' , 'serviceNotes
            Related to Resolutions:
                'pk','resolutionNumber', 'resolutionFullNumber','resolutionServiceID',
                'resolutionDate', 'resolutionEstimatedDate', 'resolutionOnQueuedDate' ,
                'resolutionOnInProgressDate' , 'resolutionDeliveryDate' ,
                'resolutionNotes', 'resolutionPipelines'
            Related to Samples:
                'runName', 'projectName', 'sampleName' , 'samplePath'
"""


if __name__ == "__main__":
    sys.exit(main())
