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

# from bdb import set_trace
import json
import sys
import sysrsync

import argparse

from drylab_api import RestServiceApi


def parser_args(args=None):
    Description = "Copy resolution FOLDER to sftp"
    Epilog = """Example usage: python copy_sftp.py --source /home/erika.kvalem/Documents/BU_ISCIII/pruebas_source/ --destination /home/erika.kvalem/Documents/BU_ISCIII/prubas_destination --options -r --exclusions "*_NC" """

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
        required=False,
        default=None,
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
    sysrsync.run(
        source=args.source,
        destination=args.destination,
        options=data["options"],
        exclusions=data["exclusions"],
        sync_source_contents=False,
    )

    # Change status in iskylims
    # rest_api = RestServiceApi("drylab/api/", "https://iskylims.isciiides.es/")


# import pdb

# pdb.set_trace()


# services_queue = rest_api.put_request("resolution/", "state", "Delivery")

# services_queue = rest_api.get_request("serviceFullData", "service", "service_number")


# def put_request(self, request_info, parameter, value):


if __name__ == "__main__":
    sys.exit(main())
