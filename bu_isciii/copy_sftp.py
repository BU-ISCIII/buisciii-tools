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


# Copy delivery to sftp (e.g: SARS service)
# Deliver automatization
# Copy in sftp
from asyncio import protocols
import json
import sys
import sysrsync
import os

import argparse


# from drylab_api import RestServiceApi


def parser_args(args=None):
    Description = "Copy resolution files to sftp"
    Epilog = """Example usage: python copy_sftp.py --source /home/erika.kvalem/Documents/BU_ISCIII/pruebas_source --destination /home/erika.kvalem/Documents/BU_ISCIII/prubas_destination --options -r --exclusions "*_NC" """

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


# Get the current working directory
cwd = os.getcwd()


def main(args=None):
    args = parser_args(args)
    sysrsync.run(
        source=args.source,
        destination=args.destination,
        options=data["options"],
        exclusions=data["exclusions"],
    )


"""
 sysrsync.run(source='/data/bi/services_and_colaborations/CNM/virologia/',
 destination='/data/bi/sftp/Labvirusres'+ service_number,
 options=["-rlpv","--update","-L","--inplace"],
 exclusions=["*_NC","lablog","work","00-reads","*.sh",".nextflow*","*_DEL","*.R","*.py" ])
 command1 = {
  "protocol":"rsync",
  "options":["-rlpv","--update","-L","--inplace"],
  "exclusions":["*_NC","lablog","work","00-reads","*.sh",".nextflow*","*_DEL","*.R","*.py"],
  "destination":"/data/bi/sftp/Labvirusres/SRVCNM572_20220209_SARSCOV278_icasas_S",
  "source":"/data/bi/services_and_colaborations/CNM/virologia/",
  "service_number":"SRVCNM572_20220209_SARSCOV278_icasas_S"
"""


if __name__ == "__main__":
    sys.exit(main())
