#!/usr/bin/env python

# Generic imports
import sys
import re
import os
import logging
import glob
import json
import shutil
import rich
import subprocess
from collections import defaultdict

# Local imports
import buisciii
import buisciii.utils
import buisciii.config_json
import buisciii.service_json
import buisciii.drylab_api

log = logging.getLogger(__name__)

stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


class NewService:
    def __init__(
        self,
        resolution_id=None,
        path=None,
        no_create_folder=None,
        ask_path=False,
        api_user=None,
        api_password=None,
        conf=None,
        setup_logging_cb=None,
    ):
        if resolution_id is None:
            self.resolution_id = buisciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        if no_create_folder is None:
            self.no_create_folder = buisciii.utils.prompt_skip_folder_creation()
        else:
            self.no_create_folder = no_create_folder

        # Load conf
        self.conf = conf.get_configuration("new_service")
        conf_api = conf.get_configuration("xtutatis_api_settings")
        # Obtain info from iSkyLIMS API
        self.rest_api = buisciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"], api_user, api_password
        )
        self.resolution_info = self.rest_api.get_request(
            request_info="service-data", safe=True, resolution=self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutions"][0][
            "resolution_full_number"
        ]
        self.services_requested = self.resolution_info["resolutions"][0][
            "available_services"
        ]
        self.service_samples = self.resolution_info.get("samples")

        if ask_path and path is None:
            stderr.print(
                "Write the directory where you want to create the service folder."
            )
            self.path = buisciii.utils.prompt_path(msg="Path")
        elif path == "-a":
            message = "ERROR: Either give a path or make the terminal ask you for a path, not both."
            stderr.print(f"[red]{message}")
            log.error(message)
            raise ValueError(
                "Either give a path or make the terminal ask you for a path, not both."
            )
        elif path is not None and ask_path is False:
            self.path = path
        elif path is not None and ask_path is not False:
            message = "ERROR: Either give a path or make the terminal ask you for a path, not both."
            stderr.print(f"[red]{message}")
            log.error(message)
            raise ValueError(
                "Either give a path or make the terminal ask you for a path, not both."
            )
        else:
            self.path = buisciii.utils.get_service_paths(
                conf,
                "services_and_colaborations",
                self.resolution_info,
                "non_archived_path",
            )
        self.full_path = os.path.join(self.path, self.service_folder)
        self.setup_logging_cb = setup_logging_cb

    def check_md5(self):
        """
        Description:
            Verify MD5 checksums of FASTQ files for all service samples grouped by sequencing project.
        """
        samples_by_project = defaultdict(list)
        for sample in self.service_samples:
            samples_by_project[sample["project_name"]].append(sample)

        for project_name, samples in samples_by_project.items():
            md5_file_path = (
                f'{self.conf["fastq_repo"]}/{project_name}/md5sum_{project_name}.md5'
            )
            if not os.path.exists(md5_file_path):
                message = f"ERROR: .md5 file not found at {md5_file_path}"
                stderr.print(f"[red]{message}")
                log.error(message)

            sample_names_pattern = "|".join(
                [re.escape(s["sample_name"]) + ".*\\.fastq\\.gz" for s in samples]
            )

            log.info(f"Checking MD5 integrity for {md5_file_path}...")
            stderr.print(f"Checking MD5 integrity for {md5_file_path}...")

            try:
                cmd = f"grep -E '{sample_names_pattern}' {md5_file_path} | md5sum -c -"
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    cwd=os.path.dirname(md5_file_path),
                    executable="/bin/bash",
                )
                message = "MD5 check passed!"
                stderr.print(f"[green]{message}")
                log.info(message)

            except subprocess.CalledProcessError:
                message = f"ERROR: MD5 check failed for project {project_name}"
                stderr.print(f"[red]{message}")
                log.error(message)
                raise

    def create_folder(self):
        """
        Description:
            Create the service directory unless folder creation is disabled.
        """
        if not self.no_create_folder:
            log.info(
                f"The service folder for {self.resolution_id} will be now created."
            )
            stderr.print(
                f"The service folder for {self.resolution_id} will be now created."
            )
            if os.path.exists(self.full_path):
                message = f"ERROR: the service folder already exists. Skipping folder creation '{self.full_path}' and exiting."
                stderr.print(f"[red]{message}")
                log.error(message)
                raise FileExistsError(
                    f"The service folder already exists. Skipping folder creation '{self.full_path}' and exiting."
                )
            else:
                try:
                    os.mkdir(self.full_path)
                except OSError:
                    message = (
                        f"ERROR: Creation of the directory '{self.full_path}' failed"
                    )
                    stderr.print(f"[red]{message}")
                    log.error(message)
                    raise
                else:
                    message = f"Successfully created the directory '{self.full_path}'"
                    stderr.print(f"[green]{message}")
                    log.info(message)
            return True
        else:
            stderr.print("[yellow]Assuming folder already exists! Moving forward!")
            log.info("Assuming folder already exists! Moving forward!")
            return False

    def copy_template(self):
        """
        Description:
            Copy the service template directories into the service folder.
        """
        log.info(
            f"The template service folders for '{self.full_path}' will now be copied into the service directory"
        )
        stderr.print(
            f"The template service folders for '{self.full_path}' will now be copied into the service directory"
        )
        services_ids = buisciii.utils.get_service_ids(self.services_requested)
        services_json = buisciii.service_json.ServiceJson()
        for service_id in services_ids:
            try:
                service_template = services_json.get_find(service_id, "template")
            except KeyError:
                message = f"ERROR: Service ID {service_id} not found in the services.json file!"
                stderr.print(f"[red]{message}")
                log.error(message)
                raise
            try:
                shutil.copytree(
                    os.path.join(
                        os.path.dirname(__file__), "templates", service_template
                    ),
                    self.full_path,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("README", "__pycache__"),
                )
                log.info(
                    f"Successfully copied the template {service_template} to the directory '{self.full_path}'!"
                )
                stderr.print(
                    f"[green]Successfully copied the template '{service_template}' to the directory '{self.full_path}'!"
                )
            except OSError:
                message = "ERROR: Copying template failed!"
                stderr.print(f"[red]{message}")
                log.error(message)
                raise
        return True

    def create_samples_id(self):
        """
        Description:
            Generate a samples_id.txt file listing all sample names for the service.
        """
        samples_id = os.path.join(self.full_path, "ANALYSIS", "samples_id.txt")
        if os.path.exists(samples_id):
            os.remove(samples_id)
        for sample in self.service_samples:
            with open(
                samples_id,
                "a",
                encoding="utf-8",
            ) as f:
                line = sample["sample_name"] + "\n"
                f.write(line)

    def create_symbolic_links(self):
        """
        Description:
            Create symbolic links to FASTQ files for all samples in the RAW directory.
        """
        samples_files = []
        for sample in self.service_samples:
            regex = os.path.join(
                self.conf["fastq_repo"], sample["project_name"], "{}_*"
            ).format(sample["sample_name"])
            sample_file = glob.glob(regex)

            if sample_file:
                samples_files.append(sample_file)
            else:
                message = f"This regex has not outputted any files: {regex}. This may be because the project is not yet in fastq_repo or because some of the samples are not in the project."
                stderr.print(f"[red]{message}")
                log.error(message)

        log.info(
            f"This service has {len(self.service_samples)} selected samples in iSkyLIMS"
        )
        log.info(f"{len(samples_files)} samples were found to create symbolic links")
        stderr.print(
            f"[blue]Service has {len(self.service_samples)} selected samples in iSkyLIMS"
        )
        stderr.print(
            f"[blue]{len(samples_files)} samples were found to create symbolic links"
        )

        if len(self.service_samples) != len(samples_files):
            if not buisciii.utils.prompt_yn_question(
                "Do you want to continue with the service creation?", dflt=True
            ):
                message = "Bye!"
                log.info(message)
                stderr.print(message)
                sys.exit()

        for sample in samples_files:
            for file in sample:
                try:
                    os.symlink(
                        file,
                        os.path.join(self.full_path, "RAW", os.path.basename(file)),
                    )
                except OSError:
                    message = f"ERROR: Symbolic links creation failed for file {file}"
                    stderr.print(f"[red]{message}")
                    log.error(message)
                    raise

    def samples_json(self):
        """
        Description:
            Write a JSON file containing all service sample data into the RAW directory.
        """
        json_samples = json.dumps(self.service_samples, indent=4)
        json_file_name = self.resolution_id + ".json"
        json_samples_file = os.path.join(
            self.path, self.service_folder, "RAW", json_file_name
        )
        try:
            with open(json_samples_file, "w") as f:
                f.write(json_samples)
            stderr.print(f"Created samples JSON file: {json_samples_file}")
            log.info(f"Created samples JSON file: {json_samples_file}")
        except Exception:
            message = "Error creating samples JSON file"
            log.error(message)
            stderr.print(f"[red]{message}")
            raise

    def create_new_service(self):
        """
        Description:
            Run the whole service creation workflow.
        """
        if len(self.service_samples) > 0:
            if self.setup_logging_cb is not None:
                self.setup_logging_cb(self.full_path)
            self.check_md5()
            self.create_folder()
            self.copy_template()
            self.create_samples_id()
            self.create_symbolic_links()
            self.samples_json()

            if self.resolution_info["service_state"] != "in_progress":
                try:
                    self.rest_api.put_request(
                        "update-state",
                        "resolution",
                        self.resolution_id,
                        "state",
                        "in_progress",
                    )
                    stderr.print(
                        f"Updated service state to 'in_progress' for {self.resolution_id}"
                    )
                    log.info(
                        f"Updated service state to 'in_progress' for {self.resolution_id}"
                    )
                except Exception:
                    stderr.print("[yellow]Could not update service state")
                    log.warning("Could not update service state")
                    raise

        else:
            message = f"WARNING: No samples recorded in service: {self.resolution_id}"
            log.warning(message)
            stderr.print(f"[yellow]{message}")

            if buisciii.utils.prompt_yn_question(
                "Do you want to proceed?: ", dflt=True
            ):
                self.create_folder()

                if self.setup_logging_cb is not None:
                    self.setup_logging_cb(self.full_path)

                self.copy_template()

                if self.resolution_info["service_state"] != "in_progress":
                    try:
                        self.rest_api.put_request(
                            "update-state",
                            "resolution",
                            self.resolution_id,
                            "state",
                            "in_progress",
                        )
                        stderr.print(
                            f"Updated service state to 'in_progress' for {self.resolution_id}"
                        )
                        log.info(
                            f"Updated service state to 'in_progress' for {self.resolution_id}"
                        )
                    except Exception:
                        stderr.print("[yellow]Could not update service state")
                        log.warning("Could not update service state")
                        raise
            else:
                message = "Directory not created. Bye!"
                log.info(message)
                stderr.print(f"[yellow]{message}")
                sys.exit()

    def get_resolution_id(self):
        """
        Description:
            Return the resolution ID associated with the service.
        """
        return self.resolution_id

    def get_service_folder(self):
        """
        Description:
            Return the name of the service folder for the given resolution.
        """
        return self.service_folder
