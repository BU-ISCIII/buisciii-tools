#!/usr/bin/env python

# Generic imports
import os
import subprocess
import logging
import re

import rich
import shutil

# Local imports
import bu_isciii
import bu_isciii.utils
from bu_isciii.drylab_api import RestServiceApi
import bu_isciii.config_json

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)


class Scratch:
    def __init__(
        self,
        resolution_id=None,
        service_dir=None,
        tmp_dir=None,
        direction=None,
    ):
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        if service_dir is None:
            self.service_dir = bu_isciii.utils.prompt_service_dir_path()
        else:
            self.service_dir = service_dir

        if tmp_dir is None:
            self.tmp_dir = bu_isciii.utils.prompt_tmp_dir_path()
        else:
            self.tmp_dir = tmp_dir

        if direction is None:
            self.direction = bu_isciii.utils.prompt_selection(
                "Select:",
                ["Service_to_scratch", "Scratch_to_service", "Remove_scratch"],
            )
        else:
            self.direction = direction

        self.rsync_command = bu_isciii.config_json.ConfigJson().get_find(
            "scratch_copy", "command"
        )
        # Load conf
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")
        # Obtain info from iskylims api
        rest_api = RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )
        self.resolution_info = rest_api.get_request(
            "resolution", "resolution", self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutionFullNumber"]
        self.scratch_path = os.path.join(self.tmp_dir, self.service_folder)
        self.out_file = os.path.join(
            self.tmp_dir, self.scratch_path, "DOC", "service_info.txt"
        )

    def copy_scratch(self):
        stderr.print("[blue]I will copy the service from %s" % self.service_dir)
        stderr.print("[blue]to %s" % self.scratch_path)
        if self.service_folder in self.service_dir:
            rsync_command = self.rsync_command + self.service_dir + " " + self.tmp_dir
            try:
                subprocess.run(rsync_command, shell=True, check=True)
                f = open(self.out_file, "a")
                f.write("Temporal directory: " + self.scratch_path + "\n")
                f.write("Origin service directory: " + self.service_dir + "\n")
                f.close()
                stderr.print(
                    "[green]Successfully copyed the directory to %s"
                    % self.scratch_path,
                    highlight=False,
                )
            except subprocess.CalledProcessError:
                stderr.print(
                    "[red]ERROR: Copy of the directory %s failed" % self.service_dir,
                    highlight=False,
                )
        else:
            log.error(
                f"Directory path not the same as service resolution. Skip folder copy '{self.service_dir}'"
            )
            stderr.print(
                "[red]ERROR: Directory "
                + self.service_dir
                + " not the same as "
                + self.service_folder,
                highlight=False,
            )
        return True

    def revert_copy_scratch(self):
        stderr.print("[blue]I will copy back the service from %s" % self.scratch_path)
        try:
            f = open(self.out_file, "r")
            for line in f:
                if re.search("Origin service directory:", line):
                    dest_folder = "".join(line.split()[3])
                    dest_dir = os.path.normpath("/".join(dest_folder.split("/")[:-1]))
            stderr.print("[blue]to %s" % dest_folder)
            if self.service_folder in dest_folder:
                rsync_command = self.rsync_command + self.scratch_path + " " + dest_dir
                subprocess.run(rsync_command, shell=True, check=True)
                stderr.print(
                    "[green]Successfully copyed the directory to %s" % dest_folder,
                    highlight=False,
                )
            else:
                log.error(
                    f"Directory path not the same as service resolution. Skip folder copy '{dest_folder}'"
                )
                stderr.print(
                    "[red]ERROR: Directory "
                    + dest_folder
                    + " not the same as "
                    + self.service_dir,
                    highlight=False,
                )
        except OSError:
            stderr.print(
                "[red]ERROR: %s does not exist" % self.out_file,
                highlight=False,
            )
        return True

    def remove_scratch(self):
        stderr.print("[blue]I will remove the folder %s" % self.scratch_path)
        try:
            f = open(self.out_file, "r")
            for line in f:
                if re.search("Temporal directory:", line):
                    scratch_folder = "".join(line.split()[2])
            f.close()

        except OSError:
            stderr.print(
                "[red]ERROR: %s does not exist" % self.out_file,
                highlight=False,
            )
        if self.service_folder in scratch_folder:
            shutil.rmtree(scratch_folder)
            stderr.print(
                "[green]Successfully removed the directory %s" % scratch_folder,
                highlight=False,
            )
        else:
            log.error(
                f"Directory path not the same as service resolution. Skip folder copy '{scratch_folder}'"
            )
            stderr.print(
                "[red]ERROR: Directory "
                + scratch_folder
                + " not the same as "
                + self.scratch_path,
                highlight=False,
            )
        return True

    def handle_scratch(self):
        if self.direction == "Service_to_scratch":
            self.copy_scratch()
        elif self.direction == "Scratch_to_service":
            self.revert_copy_scratch()
        elif self.direction == "Remove_scratch":
            self.remove_scratch()
