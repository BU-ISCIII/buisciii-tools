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
import json
import sys
import sysrsync


import argparse

# import requests

from drylab_api import RestServiceApi

class Deliver:
    def __init__(
        self,
        source=,
        destination=,
        
    ):
path = open("schemas/schema_sftp_copy.json")
data = json.load(path)


    def copy_sftp:

        path = open("schemas/schema_sftp_copy.json")
        data = json.load(path)


        sysrsync.run(
        source=args.source,
        destination=args.destination,
        options=data["options"],
        exclusions=data["exclusions"],
        sync_source_contents=False,
    )

