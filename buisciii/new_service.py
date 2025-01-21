#!/usr/bin/env python

# Generic imports
import sys
import os
import logging
import glob
import json
import shutil
import rich
import subprocess

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
        # Obtain info from iskylims api
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
            stderr.print("Directory where you want to create the service folder.")
            self.path = buisciii.utils.prompt_path(msg="Path")
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
            self.path = buisciii.utils.get_service_paths(
                conf,
                "services_and_colaborations",
                self.resolution_info,
                "non_archived_path",
            )
        self.full_path = os.path.join(self.path, self.service_folder)

    def check_md5(self):
        # Path to the .md5 file
        project_name = self.service_samples[0]["project_name"]
        md5_file_path = (
            f'{self.conf["fastq_repo"]}/{project_name}/md5sum_{project_name}.md5'
        )
        if not os.path.exists(md5_file_path):
            stderr.print(f"[red]ERROR: .md5 file not found at {md5_file_path}")
            sys.exit(1)

        original_dir = os.getcwd()
        md5_dir = os.path.dirname(md5_file_path)
        os.chdir(md5_dir)

        # Regex pattern to match sample names in .fastq.gz files
        sample_names_pattern = "|".join(
            [
                f"{sample['sample_name']}.*\\.fastq\\.gz"
                for sample in self.service_samples
            ]
        )

        # md5sum command
        stderr.print(f"[blue]Checking MD5 integrity for {md5_file_path}")
        try:
            cmd = f"grep -E '{sample_names_pattern}' {md5_file_path} | md5sum -c"
            subprocess.run(cmd, shell=True, check=True, executable="/bin/bash")
            stderr.print("[green]MD5 check passed!")
        except subprocess.CalledProcessError as e:
            stderr.print(f"[red]ERROR: MD5 check failed: {e.stderr}")
            sys.exit(1)
        finally:
            os.chdir(original_dir)

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
        services_ids = buisciii.utils.get_service_ids(self.services_requested)
        services_json = buisciii.service_json.ServiceJson()
        for service_id in services_ids:
            try:
                service_template = services_json.get_find(service_id, "template")
            except KeyError as e:
                stderr.print(
                    "[red]ERROR: Service id %s not found in services json file."
                    % service_id
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
                line = sample["sample_name"] + "\n"
                f.write(line)

    def create_symbolic_links(self):
        samples_files = []
        for sample in self.service_samples:
            regex = os.path.join(
                self.conf["fastq_repo"], sample["project_name"], "{}_*"
            ).format(sample["sample_name"])
            sample_file = glob.glob(regex)

            if sample_file:
                samples_files.append(sample_file)
            else:
                stderr.print(
                    "[red] This regex has not output any file: %s." % regex,
                    "This maybe because the project is not yet in the fastq repo"
                    "or because some of the samples are not in the project.",
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
            if not buisciii.utils.prompt_yn_question(
                "Do you want to continue with the service creation?", dflt=True
            ):
                stderr.print("Bye!")
                sys.exit()
        for sample in samples_files:
            for file in sample:
                try:
                    os.symlink(
                        file,
                        os.path.join(self.full_path, "RAW", os.path.basename(file)),
                    )
                except OSError as e:
                    stderr.print(
                        "[red]ERROR: Symbolic links creation failed for file %s." % file
                    )
                    stderr.print("Traceback: %s" % e)

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
        if len(self.service_samples) > 0:
            self.check_md5()
            self.create_folder()
            self.copy_template()
            self.create_samples_id()
            self.create_symbolic_links()
            self.samples_json()
            if self.resolution_info["service_state"] != "in_progress":
                self.rest_api.put_request(
                    "update-state",
                    "resolution",
                    self.resolution_id,
                    "state",
                    "in_progress",
                )

        else:
            stderr.print(
                "[yellow]WARN: No samples recorded in service: " + self.resolution_id
            )
            if buisciii.utils.prompt_yn_question(
                "Do you want to proceed?: ", dflt=True
            ):
                self.create_folder()
                self.copy_template()
                if self.resolution_info["service_state"] != "in_progress":
                    self.rest_api.put_request(
                        "update-state",
                        "resolution",
                        self.resolution_id,
                        "state",
                        "in_progress",
                    )
            else:
                stderr.print("Directory not created. Bye!")
                sys.exit(1)

    def get_resolution_id(self):
        return self.resolution_id

    def get_service_folder(self):
        return self.service_folder
