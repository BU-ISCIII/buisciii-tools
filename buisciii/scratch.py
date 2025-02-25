#!/usr/bin/env python

# Generic imports
import sys
import os
import logging
import re
import subprocess
import sysrsync

import rich
import shutil

# Local imports
import buisciii
import buisciii.utils
import buisciii.drylab_api
import buisciii.config_json

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


class Scratch:
    def __init__(
        self,
        resolution_id=None,
        path=None,
        tmp_dir=None,
        direction=None,
        ask_path=False,
        api_user=None,
        api_password=None,
        conf=None,
    ):
        if resolution_id is None:
            self.resolution_id = buisciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        if tmp_dir is None:
            self.tmp_dir = buisciii.utils.prompt_tmp_dir_path()
        else:
            self.tmp_dir = tmp_dir

        if direction is None:
            self.direction = buisciii.utils.prompt_selection(
                "Select:",
                ["service_to_scratch", "scratch_to_service", "remove_scratch"],
            )
        else:
            self.direction = direction
        # Load conf
        conf_api = conf.get_configuration("xtutatis_api_settings")
        # Obtain info from iskylims api
        rest_api = buisciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"], api_user, api_password
        )
        self.conf = conf.get_configuration("scratch_copy")

        self.resolution_info = rest_api.get_request(
            request_info="service-data", safe=True, resolution=self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutions"][0][
            "resolution_full_number"
        ]
        self.scratch_tmp_path = os.path.join(self.tmp_dir, self.service_folder)
        # params like --chdir, --partition and --time
        srun_params = self.conf["srun_settings"].items()
        self.srun_settings = [arg for param in srun_params for arg in param]
        if ask_path and path is None:
            stderr.print("Directory where service folder is located.")
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
        self.out_file = os.path.join(self.full_path, "DOC", "service_info.txt")

    def srun_command(self, srun_settings, command):
        command_list = [["srun"], srun_settings, command]
        srun_command = [arg for command in command_list for arg in command]
        exit_code = subprocess.call(srun_command)
        return exit_code

    def copy_scratch(self):
        stderr.print("[blue]I will copy the service from %s" % self.full_path)
        stderr.print("[blue]to %s" % self.scratch_tmp_path)
        if self.service_folder in self.full_path:
            protocol = self.conf["protocol"]
            try:
                if protocol == "rsync":
                    rsync_command = sysrsync.get_rsync_command(
                        source=self.full_path,
                        destination=self.conf["scratch_path"] + "/",
                        options=self.conf["options"],
                        exclusions=self.conf["exclusions"],
                        sync_source_contents=False,
                    )
                    exit_code = self.srun_command(self.srun_settings, rsync_command)

                else:
                    stderr.print(
                        "[ref] This protocol is not allowed at the moment",
                        highlight=False,
                    )
                    sys.exit()
                if exit_code == 0:
                    stderr.print(
                        "[green] Data copied to the sftp folder successfully",
                        highlight=False,
                    )
                    f = open(self.out_file, "w")
                    f.write("Temporal directory: " + self.scratch_tmp_path + "\n")
                    f.write("Origin service directory: " + self.full_path + "\n")
                    f.close()
                    stderr.print(
                        "[green]Successfully copied the directory to %s"
                        % self.scratch_tmp_path,
                        highlight=False,
                    )
                else:
                    stderr.print(f"[red]Errors while copying {self.full_path}")
            except Exception as e:
                stderr.print(e)
                stderr.print(
                    "[red]ERROR: Copy of the directory %s failed" % self.full_path,
                    highlight=False,
                )
                sys.exit(1)
        else:
            log.error(
                f"Directory path not the same as service resolution. Skip folder copy '{self.full_path}'"
            )
            stderr.print(
                "[red]ERROR: Directory "
                + self.full_path
                + " not the same as "
                + self.service_folder,
                highlight=False,
            )
        return True

    def revert_copy_scratch(self):
        stderr.print(f"[blue]I will copy back the service from {self.scratch_tmp_path}")
        try:
            f = open(self.out_file, "r")
            for line in f:
                if re.search("Origin service directory:", line):
                    dest_folder = "".join(line.split()[3])
                    dest_dir = os.path.normpath("/".join(dest_folder.split("/")[:-1]))
            stderr.print("[blue]to %s" % dest_folder)
            if self.service_folder in dest_folder:
                try:
                    if self.conf["protocol"] == "rsync":
                        # scratch_tmp cannot be used due to permission issues
                        scratch_bi_path = "".join(
                            [self.conf["scratch_path"], self.service_folder]
                        )
                        rsync_command = sysrsync.get_rsync_command(
                            source=scratch_bi_path,
                            destination=dest_dir,
                            options=self.conf["options"],
                            exclusions=self.conf["exclusions"],
                            sync_source_contents=False,
                        )
                        self.srun_command(self.srun_settings, rsync_command)

                        # After successful rsync, apply correct permissions
                        conf = buisciii.config_json.ConfigJson()
                        permissions_config = conf.get_configuration("global").get(
                            "permissions"
                        )
                        buisciii.utils.remake_permissions(
                            self.full_path, permissions_config
                        )

                        stderr.print(
                            "[green]Successfully copied the directory to %s"
                            % dest_folder,
                            highlight=False,
                        )
                    else:
                        stderr.print(
                            "[ref] This protocol is not allowed at the moment",
                            highlight=False,
                        )
                        sys.exit()
                except Exception as e:
                    stderr.print(e)
                    stderr.print(
                        "[red]ERROR: Copy of directory %s failed"
                        % self.scratch_tmp_path,
                        highlight=False,
                    )
                    sys.exit(1)
            else:
                log.error(
                    f"Directory path not the same as service resolution. Skip folder copy '{dest_folder}'"
                )
                stderr.print(
                    "[red]ERROR: Directory "
                    + dest_folder
                    + " not the same as "
                    + self.full_path,
                    highlight=False,
                )
        except OSError:
            stderr.print(
                "[red]ERROR: %s does not exist" % self.out_file,
                highlight=False,
            )
        return True

    def remove_scratch(self):
        stderr.print("[blue]I will remove the folder %s" % self.scratch_tmp_path)
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
                "[green]Successfully removed directory %s" % scratch_folder,
                highlight=False,
            )
        else:
            log.error(
                f"Directory path is not the same as service resolution. Skip folder copy '{scratch_folder}'"
            )
            stderr.print(
                "[red]ERROR: Directory "
                + scratch_folder
                + " is not the same as "
                + self.scratch_tmp_path,
                highlight=False,
            )
        return True

    def handle_scratch(self):
        if self.direction == "service_to_scratch":
            self.copy_scratch()
        elif self.direction == "scratch_to_service":
            self.revert_copy_scratch()
        elif self.direction == "remove_scratch":
            self.remove_scratch()
