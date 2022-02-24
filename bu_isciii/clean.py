#!/usr/bin/env python
"""
=============================================================
HEADER
=============================================================
INSTITUTION: BU-ISCIII
AUTHOR: Guillermo J. Gorines Cordero
MAIL: guillermo.gorines@urjc.es
CREATED: 21-2-2022
REVISED: 23-2-2022
DESCRIPTION:
OPTIONS:

USAGE:

REQUIREMENTS:

TO DO:
    -INIT: where to find the needed values
    -PATH: where to be placed
        -BASE_DIRECTORY: where is it? How do we know where it is?

    -DESCRIPTION
        -SCRIPT
        -CLASS
        -METHODS
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

"""
log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)
"""

class CleanUp:
    def __init__(self, resolution_id=None):
        # access the api/the json/the whatever with the service name to obtain

        if resolution_id == None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        print(self.resolution_id)
        # self.base_directory =
        # self.delete =
        # self.nocopy =
        # self.sacredtexts =
        return

    def show_removable_dirs(self, to_stdout=True):
        """
        Description:
            Print or return the list of objects that must be deleted in this service

        Usage:
            object.show_removable_dirs(to_stdout = [BOOL])

        Params:
            to_stdout [BOOL]: if True, print the list. If False, return the list.
        """
        if to_stdout:
            print(self.delete)
            return
        else:
            return self.delete

    def show_nocopy_dirs(self, to_stdout=True):
        """
        Description:
            Print or return the list of objects that must be renamed in this service

        Usage:
            object.show_nocopy_dirs(to_stdout = [BOOL])

        Params:
            to_stdout [BOOL]: if True, print the list. If False, return the list.
        """
        if to_stdout:
            print(self.nocopy)
            return
        else:
            return self.nocopy

    def scan_dirs(self, to_find):
        """
        Description:
            Parses the directory tree, and generates two lists:
                -list with the elements (dirs and files) to be deleted
                -list with the dirs to be renamed

        If a list is given as arguments, the names included
        (either files or directories) won't be included in the
        dictionary.

        Usage:
            to_rename, to_delete = object.scan_dirs(to_find=list)

        Params:

        """
        pathlist = []

        # key: root, values: [[files inside], [dirs inside]]
        for root, _, _ in os.walk(self.path):
            # coincidence might not be total so double loop by now
            for item_to_be_found in to_find:
                if item_to_be_found in root:
                    pathlist.append(root)

        return pathlist

    def rename(self, to_find, add, verbose=True):
        """
        Description:
            Rename the files and directories

        Usage:

        Params:

        """

        path_content = self.scan_dirs(to_find=to_find)

        for directory_to_rename in path_content:
            newpath = directory_to_rename + add
            os.replace(directory_to_rename, newpath)
            if verbose:
                print(f"Renamed {directory_to_rename} to {newpath}.")
        return

    def rename_nocopy(self, verbose=True):
        """
        Description:

        Usage:

        Params:

        """
        self.rename(to_find=self.nocopy, add="_NC", verbose=verbose)
        return

    def delete(self, sacredtexts=["lablog", "logs"], verbose=True):
        """
        Description:
            Remove the files that must be deleted for the delivery of the service
            Their contains, except for the lablog file, and the logs dir, will be
            deleted

        Usage:
            object.delete()

        Params:
            sacredtexts [list]: names (str) of the files that shall not be deleted.

        """

        path_content = self.scan_dirs(to_find=self.delete)
        unfiltered_items = []
        filtered_items = []

        for directory in path_content:
            # if not empty add it to the content
            if len(os.listdir(directory)) > 0:
                unfiltered_items += directory
        # take out those belonging to the sacred items
        for item in unfiltered_items:
            # coincidence might not be total so double loop
            for text in sacredtexts:
                # add it to the filtered list if not in the sacredtext
                if text not in item:
                    filtered_items.append(item)

        for item in filtered_items:
            # shutil if dir, os.remove if file
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
            if verbose:
                print(f"Removed {item}.")
        return

    def delete_rename(self, verbose=True, sacredtexts=["lablog", "logs"]):
        self.delete(sacredtexts=sacredtexts, verbose=verbose)
        self.rename(add="_DEL", to_find=self.delete, verbose=verbose)

    def revert_renaming(self, verbose=True, terminations=["_DEL", "_NC"]):
        """
        Description:
        Reverts the naming (adding of the _NC tag)

        Usage:

        Params:

        """
        to_rename = self.scan_dirs(to_find=terminations)
        for dir_to_rename in to_rename:
            # remove all the terminations
            for term in terminations:
                newname = dir_to_rename.replace(term, "")
            os.replace(dir_to_rename, newname)
            if verbose:
                print(f"Replaced {dir_to_rename} with {newname}.")

    def full_clean_job(self):

        """
        Perform the whole cleaning of the service
        """
        # if '_NC' in ____ or '_DEL' in ___:
        # print that a previous usage of this was detected
        # self.rename()
        # self.delete()

        return

# Testing zone

testing_object = CleanUp("SRVCNM552.1")