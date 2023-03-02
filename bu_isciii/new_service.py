#!/usr/bin/env python

# Generic imports
import sys
import os
import logging
import glob
import json
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
        self,
        resolution_id=None,
        path=None,
        no_create_folder=None,
        ask_path=False,
        api_password=None,
    ):
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        if no_create_folder is None:
            self.no_create_folder = bu_isciii.utils.prompt_skip_folder_creation()
        else:
            self.no_create_folder = no_create_folder

        # Load conf
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("new_service")
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration(
            "xtutatis_api_settings"
        )
        # Obtain info from iskylims api
        self.rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"], api_password
        )
        self.resolution_info = self.rest_api.get_request(
            "serviceFullData", "resolution", self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutions"][0][
            "resolutionFullNumber"
        ]
        self.services_requested = self.resolution_info["resolutions"][0][
            "availableServices"
        ]
        self.service_samples = self.resolution_info["samples"]

        if ask_path and path is None:
            stderr.print("Directory where you want to create the service folder.")
            self.path = bu_isciii.utils.prompt_path(msg="Path")
        elif path == "-a":
            stderr.print(
                "[red] ERROR: Either give a path or make the terminal ask you a path, not both."
            )
            sys.exit()
        elif path is not None and ask_path is False:
            self.path = path
        elif path is not None and ask_path is not False:
            stderr.print(
                "[red] ERROR: Either give a path or make the terminal ask you a path, not both."
            )
            sys.exit()
        else:
            self.path = bu_isciii.utils.get_service_paths(self.resolution_info)

        self.full_path = os.path.join(self.path, self.service_folder)

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
        services_ids = bu_isciii.utils.get_service_ids(self.services_requested)
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
                    ignore=shutil.ignore_patterns("README", "__pycache__"),
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
        samples_files = []
        for sample in self.service_samples:
            regex = os.path.join(
                self.conf["fastq_repo"], sample["projectName"], "{}*"
            ).format(sample["sampleName"])
            sample_file = glob.glob(regex)
            if sample_file:
                samples_files.appned(sample_file)
            else:
                stderr.print(
                    "[red] This regex has not output any file: %s. This maybe because the project is not yet in the fastq repo or because some of the samples are not in the project."
                    % regex
                )
        stderr.print(
            "[blue] Service has %s number of selected samples in iSkyLIMS"
            % len(self.service_samples)
        )
        stderr.print(
            "[blue] %s number of samples where found to create symbolic links"
            % len(samples_files)
        )
        if len(self.service_samples) != len(samples_files):
            if not bu_isciii.utils.prompt_yn_question(
                "Do you want to continue with the service creation?"
            ):
                stderr.print("Bye!")
                sys.exit()
        for file in samples_files:
            try:
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
                sys.exit()

    def samples_json(self):
        json_samples = json.dumps(self.service_samples, indent=4)
        json_file_name = self.resolution_id + ".json"
        json_samples_file = os.path.join(
            self.path, self.service_folder, "RAW", json_file_name
        )
        f = open(json_samples_file, "w")
        f.write(json_samples)
        f.close()

    def create_new_service(self):
        self.create_folder()
        self.copy_template()
        self.create_samples_id()
        self.create_symbolic_links()
        self.samples_json()
        self.rest_api.put_request(
            "updateState", "resolution", self.resolution_id, "state", "In%20Progress"
        )

    def get_resolution_id(self):
        return self.resolution_id

    def get_service_folder(self):
        return self.service_folder
