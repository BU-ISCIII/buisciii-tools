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
import sys
import os
import logging

import shutil
import rich

# Local imports
import bu_isciii
import bu_isciii.utils
from bu_isciii.service_json import ServiceJson
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
        self, resolution_id=None, path=None, no_create_folder=None, ask_path=False
    ):
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        if ask_path:
            self.path = bu_isciii.utils.prompt_path()
        else:
            self.path = path

        if no_create_folder is None:
            self.no_create_folder = bu_isciii.utils.prompt_skip_folder_creation()
        else:
            self.no_create_folder = no_create_folder

        rest_api = RestServiceApi("http://iskylims.isciiides.es/", "drylab/api/")
        self.resolution_info = rest_api.get_request(
            "resolution", "resolution", self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutionFullNumber"]
        self.services_requested = self.resolution_info["availableServices"]
        self.full_path = os.path.join(path, self.path, self.service_folder)

    def get_service_ids(self):
        service_id_list = []
        for services in self.services_requested:
            service_id_list.append(services["serviceId"])
        service_id_list.append("all")
        services_sel = [bu_isciii.utils.prompt_service_selection(service_id_list)]
        if services_sel == "all":
            services_sel == service_id_list
        return services_sel

    def create_folder(self):
        print("I will create the service folder for " + self.resolution_id + "!")
        if os.path.exists(self.full_path):
            log.error(f"Directory exists. Skip folder creation '{self.full_path}'")
            stderr.print(
                "[red]ERROR: Directory " + self.full_path + " exists",
                highlight=False,
            )
        else:
            try:
                os.mkdir(self.full_path)
            except OSError:
                stderr.print(
                    "[red]ERROR: Creation of the directory %s failed" % self.full_path,
                    highlight=False,
                )
            else:
                stderr.print(
                    "[green]Successfully created the directory %s" % self.full_path,
                    highlight=False,
                )
        return True

    def copy_template(self):
        stderr.print(
            "[blue]I will copy the template service folders for %s !" % self.full_path
        )
        services_ids = self.get_service_ids()
        services_json = ServiceJson()
        if len(services_ids) == 1:
            try:
                service_template = services_json.get_find(services_ids[0], "template")
            except KeyError as e:
                stderr.print(
                    "[red]ERROR: Service id %s not found in services json file."
                    % services_ids[0]
                )
                stderr.print("traceback error %s" % e)
                sys.exit()
            try:
                shutil.copytree(
                    os.path.join(
                        os.path.dirname(__file__), "templates", service_template[0]
                    ),
                    self.full_path,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("README"),
                )
            except OSError as e:
                stderr.print("[red]ERROR: Copying template failed.")
                stderr.print("traceback error %s" % e)
                sys.exit()
        else:
            stderr.print(
                "[red] ERROR: I'm not already prepared for handling more than one error at the same time, sorry! Please re-run and select one of the service ids."
            )
            sys.exit()
            return False
        return True

    def get_resolution_id(self):
        return self.resolution_id

    def get_service_folder(self):
        return self.service_folder
