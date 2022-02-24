#!/usr/bin/env python
"""
=============================================================
HEADER
=============================================================
INSTITUTION: BU-ISCIII
AUTHOR: Sara Monzon; Sarai Varona
MAIL: smonzon@isciii.es; s.varona@isciii.es
CREATED: 24-02-2022
DESCRIPTION:
OPTIONS:

USAGE:

REQUIREMENTS:

TO DO:
    -copy_scratch: Change rsync to the one in the slurm hpc
================================================================
END_OF_HEADER
================================================================
"""
# Generic imports
import os
import subprocess
import logging

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


class Scratch:
    def __init__(
        self,
        resolution_id=None,
        source=None,
        destination=None,
    ):
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        if source is None:
            self.source = bu_isciii.utils.prompt_source_path()
        else:
            self.source = source

        if destination is None:
            self.destination = bu_isciii.utils.prompt_destination_path()
        else:
            self.destination = destination

        rest_api = RestServiceApi("http://iskylims.isciiides.es/", "drylab/api/")
        self.resolution_info = rest_api.get_request(
            "resolution", "resolution", self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutionFullNumber"]
        self.dest_path = os.path.join(
            destination, self.destination, self.service_folder
        )

    def copy_scratch(self):
        stderr.print("[blue]I will copy the service from %s" % self.source)
        stderr.print("[blue]to %s" % self.dest_path)
        if self.service_folder in self.source:
            rsync_command = "rsync -rlv " + self.source + " " + self.destination
            # rsync_command = "srun rsync -rlv "+self.source+" "+self.destination
            try:
                subprocess.run(rsync_command, shell=True, check=True)
            except OSError:
                stderr.print(
                    "[red]ERROR: Copy of the directory %s failed" % self.source,
                    highlight=False,
                )
            else:
                stderr.print(
                    "[green]Successfully copyed the directory to %s" % self.dest_path,
                    highlight=False,
                )
        else:
            log.error(
                f"Directory path not the same as service resolution. Skip folder copy '{self.source}'"
            )
            stderr.print(
                "[red]ERROR: Directory "
                + self.source
                + " not the same as "
                + self.service_folder,
                highlight=False,
            )
        return True
