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
import sys
import os
import logging
import shutil
from rich.console import Console

# Local imports
import bu_isciii
import bu_isciii.utils
from bu_isciii.drylab_api import RestServiceApi
from bu_isciii.service_json import ServiceJson

log = logging.getLogger(__name__)
stderr = Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)


class CleanUp:
    def __init__(self, resolution_id=None):
        """
        Description:
            Class to perform the cleaning.

        Usage:

        Attributes:

        Methods:

        """
        # access the api with the resolution name to obtain the data
        # ask away if no input given
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id
        # get the service id from the resolution_id
        rest_api = RestServiceApi("http://iskylims.isciiides.es/", "drylab/api/")
        resolution_dict = rest_api.get_request(
            "resolution", "resolution", self.resolution_id
        )

        self.theoretical_path = resolution_dict["resolutionFullNumber"]

        all_service_ids = resolution_dict["availableServices"]
        # from dict to list
        self.service_id = [item["serviceId"] for item in all_service_ids]
        choice_num = len(self.service_id)
        if choice_num > 1:
            # ask which service id based on the resolution
            stderr.print(f"I found {choice_num} different service IDs.")
            self.service_id = bu_isciii.utils.prompt_selection(
                "Please choose the proper one:", self.service_id
            )
        else:
            self.service_id = "".join(self.service_id)

        # once chosen the service_id, find the delete and nocopy directories
        srv_json = ServiceJson()

        # harcorded for testing
        # this line MUST be removed
        self.service_id = "assembly_annotation"

        # get the dict of that very service id
        service_id_dict = srv_json.get_service_configuration(self.service_id)

        # generate the list of items to delete
        self.delete_list = []
        clean_dict = service_id_dict["clean"]

        for item in clean_dict.values():
            self.delete_list += item

        # remove empty strings
        self.delete_list = [item for item in self.delete_list if item]

        elements = ", ".join(self.delete_list)
        stderr.print(f"The following entities will be deleted: {elements}")
        if not bu_isciii.utils.prompt_yn_question("Is it okay?"):
            stderr.print("You got it.")
            sys.exit()

        # generate the list of items to add the "_NC" to
        self.nocopy_list = service_id_dict["no_copy"]
        elements = ", ".join(self.nocopy_list)

        # ask away if thats ok
        stderr.print(f"The following directories will be renamed: {elements}")
        if not bu_isciii.utils.prompt_yn_question("Is it okay?"):
            stderr.print("You are the boss here.")
            sys.exit()

        # ask where to perform (get the full path)
        stderr.print("Where should I clean?")
        self.base_directory = os.path.abspath(bu_isciii.utils.prompt_path("Path"))

        # if the theoretical name is not found, then bye
        if (
            self.theoretical_path not in self.base_directory
            and self.theoretical_path not in os.listdir(self.base_directory)
        ):
            stderr.print(
                "Seems like finding the correct path is beneath me. I apologise."
            )
            sys.exit()

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
            stderr.print(self.delete_list)
            return
        else:
            return self.delete_list

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
            stderr.print(self.nocopy_list)
            return
        else:
            return self.nocopy_list

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

    def delete(self, sacredtexts=["lablog", "logs"], add="", verbose=True):
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
            # if not empty, and not previously DEL add it to the content
            if not directory.endswith(add) and len(os.listdir(directory)) > 0:
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

    def delete_rename(self, verbose=True, sacredtexts=["lablog", "logs"], add="_DEL"):
        self.delete(sacredtexts=sacredtexts, add=add, verbose=verbose)
        self.rename(add=add, to_find=self.delete, verbose=verbose)

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
# testing_object = CleanUp("SRVCNM552.1")
