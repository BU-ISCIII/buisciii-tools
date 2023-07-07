#!/usr/bin/env python
#   sftp_autoclean.py
#
#   Gaol: automatically remove service from sftp after X days after the last update/access  
#       Sub goals:
#           1. Get user confirmation --> yes/no [prompt]
#           2. Agument -p [path] or default [resolution.id ftp path]
#           1. Get sftp service metadata from jsons
#           2. Get last access/modification date (this may be checked not only in the parent floder but also in all childrens)   
#           3. Implement logic. I condition is met then, apply auto-cleanup
#           4. Add a prortection property in order to avoid cleaning files that will be store in sftp for long-period time.
#           5. Provide a log-completition file. 
#           6. linting -- pep8 & black

# import
import os
import sys
import logging
import rich
import questionary
from datetime import datetime, timedelta

# import locals
#import buisciii.utils

# add loggin and colors

# create class

# =================================================================
# Backbone and utils
# =================================================================

# temp cp from utils
def prompt_path(msg):
    source = questionary.path(msg).unsafe_ask()
    return source

def prompt_yn_question(msg):
    confirmation = questionary.confirm(msg).unsafe_ask()
    return confirmation


use_default = prompt_yn_question( # replace with buisciii.utils.prompt_path after testing it
    "Do you want to use the default sftp path <var>?:" # get config_json keys
    )

if use_default:
    sftp_path = "home/da.valle/work/bi/test/service/"
else:
    sftp_path = prompt_path( # replace with buisciii.utils.prompt_path after testing it
    "Path to the directory containing the sftp directory: "
    )
    # Validate user's dirif the directory path exists
    while sftp_path is None or not os.path.isdir(sftp_path):
        # TODO: this print must be replaced by stderr... to be homogenous to buisciii tools
        print("Invalid directory path. Please try again.")
        sftp_path = prompt_path( # replace with buisciii.utils.prompt_path after testing it
        "Path to the directory containing the service metadata"
        )
