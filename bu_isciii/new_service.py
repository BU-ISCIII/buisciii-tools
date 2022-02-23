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
import os
import logging

import shutil
import rich

# Local imports
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


class NewService:
    def __init__(
        self,
        resolution_id=None,
        path=None,
        no_create_folder=False,
    ):
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        self.path = path
        self.no_create_folder = no_create_folder
        rest_api = RestServiceApi("http://iskylims.isciiides.es/", "drylab/api/")
        self.resolution_info = rest_api.get_request(
            "resolution", "resolution", self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutionFullNumber"]
        self.services_requested = self.resolution_info["availableServices"]
        self.full_path = os.path.join(path, self.path, self.service_folder)

    def create_folder(self):
        print("I will create the service folder for " + self.resolution_id + "!")
        isExist = os.path.exists(self.full_path)
        if isExist:
            stderr.print(
                "[red]ERROR: Directory "
                + self.full_path
                + " exists",
                highlight=False,
            )
        else:
            try:
                os.mkdir(self.full_path)
            except OSError:
                stderr.print(
                    "[red]ERROR: Creation of the directory %s failed"
                    % self.full_path,
                    highlight=False,
                )
            else:
                stderr.print(
                    "[green]Successfully created the directory %s"
                    % self.full_path,
                    highlight=False,
                )
        return True

    def copy_template(self):
        print(
            "I will copy the template service folders for " + self.full_path + "!"
        )
        # service = bu_isciii.json_reader.Service(self.service_id)
        # service_template = new_ser.get_template()
        service_template = ["viralrecon"]  # TMP!!
        if len(service_template) == 1:
            shutil.copytree(
                "templates/" + str(service_template[0]),
                self.full_path,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("README"),
            )
        return True

    def get_resolution_id(self):
        return self.resolution_id

    def get_service_folder(self):
        return self.service_folder

    def get_service_label(self):
        return self.service_label

    def get_service_id(self):
        return self.get_service_id
