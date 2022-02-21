#!/usr/bin/env python
"""
=============================================================
HEADER
=============================================================
INSTITUTION: BU-ISCIII
AUTHOR: Sara Monzon; Sarai Varona
MAIL: smonzon@isciii.es; s.varona@isciii.es
CREATED: 21-02-2022
DESCRIPTION:
OPTIONS:

USAGE:

REQUIREMENTS:

TO DO:
    -INIT: where to find the needed values
    -PATH: where to be placed
        -BASE_DIRECTORY: where is it? How do we know where it is?


    -NAMING: let's be honest, those are terrible
================================================================
END_OF_HEADER
================================================================
"""
# Generic imports
# import sys
# import os
import logging

import rich

# Local imports
import bu_isciii
import bu_isciii.utils

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)


class NewService:
    def __init__(
        self,
        resolution_id=None,
        service_folder=None,
        service_label=None,
        service_id=None,
        path=None,
        no_create_folder=False,
    ):
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        self.service_folder = service_folder
        self.service_label = service_label
        self.service_id = service_id
        self.path = path
        self.no_create_folder = no_create_folder

    def create_folder(self):
        print("I will create the service folder!")
        return True

    def copy_template(self):
        return True

    def get_resolution_id(self):
        return self.resolution_id

    def get_service_folder(self):
        return self.service_folder

    def get_service_label(self):
        return self.service_label

    def get_service_id(self):
        return self.get_service_id
