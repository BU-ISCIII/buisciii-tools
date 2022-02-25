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
================================================================
END_OF_HEADER
================================================================
"""
# Generic imports
import sys
import os
import logging
import glob

import shutil
import rich

# Local imports
import bu_isciii
import bu_isciii.utils
import bu_isciii.config_json
import bu_isciii.service_json
import bu_isciii.drylab_api

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
            self.path = os.getcwd()

        if no_create_folder is None:
            self.no_create_folder = bu_isciii.utils.prompt_skip_folder_creation()
        else:
            self.no_create_folder = no_create_folder

        # Load conf
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("new_service")
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")
        # Obtain info from iskylims api
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )
        self.resolution_info = rest_api.get_request(
            "resolutionFullData", "resolution", self.resolution_id
        )
        self.service_folder = self.resolution_info["Resolutions"][
            "resolutionFullNumber"
        ]
        self.services_requested = self.resolution_info["Resolutions"][
            "availableServices"
        ]
        self.service_samples = self.resolution_info["Samples"]
        self.full_path = os.path.join(self.path, self.service_folder)
        ###
        ### resolutionFullData example
        ###
        # {
        #    "Service": {
        #        "pk": 1551,
        #        "serviceRequestNumber": "SRVCNM564",
        #        "serviceStatus": "queued",
        #        "serviceUserId": {
        #            "username": "smonzon",
        #            "first_name": "Sara",
        #            "last_name": "Monzon",
        #            "email": "smonzon@isciii.es"
        #        },
        #        "serviceCreatedOnDate": "2022-02-24",
        #        "serviceSeqCenter": "Centro Nacional de Microbiologia",
        #        "serviceAvailableService": [
        #            "Genomic Data Analysis",
        #            "DNAseq: Exome sequencing (WES) / Genome sequencing (WGS) / Target (Amplicon, probes)  / Direct seq",
        #            "Viral: consensus, assembly and minor variants detection - Viralrecon (with reference)"
        #        ],
        #        "serviceFileExt": null,
        #        "serviceNotes": "this is for buisciii tools testing"
        #    },
        #    "Resolutions": {
        #        "pk": 1716,
        #        "resolutionNumber": "SRVCNM564.1",
        #        "resolutionFullNumber": "SRVCNM564_20220224_TESTINGBUISCIIITOOLS_smonzon_S",
        #        "resolutionServiceID": 1551,
        #        "resolutionDate": "2022-02-24",
        #        "resolutionEstimatedDate": "2022-02-25",
        #        "resolutionOnQueuedDate": "2022-02-24",
        #        "resolutionOnInProgressDate": null,
        #        "resolutionDeliveryDate": null,
        #        "resolutionNotes": "",
        #        "resolutionPipelines": [],
        #        "availableServices": [
        #            {
        #                "availServiceDescription": "Viral: consensus, assembly and minor variants detection - Viralrecon (with reference)",
        #                "serviceId": "viralrecon"
        #            }
        #        ]
        #    },
        #    "Samples": [
        #        {
        #            "runName": "NovaSeq_GEN_032",
        #            "projectName": "NovaSeq_GEN_032_20220209_RAbad",
        #            "sampleName": "9793",
        #            "samplePath": "220209_A01158_0051_AHWCJJDRXY"
        #        }
        #

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
        if not self.no_create_folder:
            stderr.print(
                "[blue]I will create the service folder for " + self.resolution_id + "!"
            )
            if os.path.exists(self.full_path):
                log.error(f"Directory exists. Skip folder creation '{self.full_path}'")
                stderr.print(
                    "[red]ERROR: Directory " + self.full_path + " exists. Exiting.",
                    highlight=False,
                )
                sys.exit()
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
                        "[green]Successfully created the directory %s" % self.full_path,
                        highlight=False,
                    )
            return True
        else:
            stderr.print("[blue]Ok assuming folder is created! Let's move forward!")
            return False

    def copy_template(self):
        stderr.print(
            "[blue]I will copy the template service folders for %s !" % self.full_path
        )
        services_ids = self.get_service_ids()
        services_json = bu_isciii.service_json.ServiceJson()
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
                        os.path.dirname(__file__), "templates", service_template
                    ),
                    self.full_path,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("README"),
                )
                stderr.print(
                    "[green]Successfully copied the template %s to the directory %s"
                    % (service_template, self.full_path),
                    highlight=False,
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

    def create_samples_id(self):
        samples_id = os.path.join(self.full_path, "ANALYSIS", "samples_id.txt")
        if os.path.exists(samples_id):
            os.remove(samples_id)
        for sample in self.service_samples:
            with open(
                samples_id,
                "a",
                encoding="utf-8",
            ) as f:
                line = sample["sampleName"] + "\n"
                f.write(line)

    def create_symbolic_links(self):
        for sample in self.service_samples:
            regex = os.path.join(
                self.conf["fastq_repo"], sample["projectName"], "{}*"
            ).format(sample["sampleName"])
            sample_files = glob.glob(regex)
            if not sample_files:
                stderr.print(
                    "[red] This regex has not output any file: %s. This maybe because the project is not yet in the fastq repo or because some of the samples are not in the project."
                    % regex
                )

            try:
                for file in sample_files:
                    os.symlink(
                        file,
                        os.path.join(self.full_path, "RAW", os.path.basename(file)),
                    )
            except OSError as e:
                stderr.print(
                    "[red]ERROR: Symbolic links creation failed for sample %s."
                    % sample["sampleName"]
                )
                stderr.print("Traceback: %s" % e)

    def create_new_service(self):
        self.create_folder()
        self.copy_template()
        self.create_samples_id()
        self.create_symbolic_links()

    def get_resolution_id(self):
        return self.resolution_id

    def get_service_folder(self):
        return self.service_folder
