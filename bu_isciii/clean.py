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

# Local imports


class CleanUp:
    def __init__(self, resolution_name):
        # access the api/the json/the whatever with the service name to obtain

        self.resolution_name = resolution_name
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

    def scan_dirs(self, to_find=[]):
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

        UNUSED CODE:
                to_rename = []
        to_delete = []
        # if must be found, add all its contents
        for directory, contentlist in path_content.items():
            if directory in to_find:
                to_rename.append(directory)
                to_delete += contentlist[0]
                to_delete += contentlist[1]
            else:
                for file in to_find:
                    if file in to_find:
                        to_delete.append(file)
                return path_content

        """
        pathlist = []

        # key: root, values: [[files inside], [dirs inside]]
        for root, _, _ in os.walk(self.path):
            # coincidence might not be total so double loop
            for item_to_be_found in to_find:
                if item_to_be_found in root:
                    pathlist.append(root)

        return pathlist

    def rename(self, add="_NC", verbose=True):
        """
        Description:
            Rename the files and directories

        Usage:

        Params:

        """

        path_content = self.scan_dirs(to_find=self.nocopy)

        for directory_to_rename in path_content:
            newpath = directory_to_rename + add
            os.replace(directory_to_rename, newpath)
            if verbose:
                print(f'Renamed {directory_to_rename} to {newpath}.')

        return

    def delete(self, verbose=True):
        """
        Description:
            Remove the files that must be deleted for the delivery of the service
            Their contains, except for the lablog file, and the logs dir, will be
            deleted

        Usage:
            object.delete()

        Params:
            sacredtexts [list]: names (str) of the files that shall not be deleted.


        UNUSED CODE:
        # might contain both dirs and files
        for thing_to_delete in to_delete:
            os.remove(thing_to_delete)
            if verbose:
                print(f'Removed {thing_to_delete}.')

        for thing_to_rename in to_rename:
            newname = thing_to_rename + '_DEL'
            os.replace(thing_to_rename, newname)
            if verbose:
                print(f'Renamed {thing_to_rename} to {newname}.')
        """

        path_content = self.scan_dirs(to_find=self.delete)
        deletable_items = []

        for directory in path_content:
            if len(os.listdir(directory)) > 0:
                deletable_items += directory
        for item in deletable_items:
            try:
                os.remove(item)
            #OSError is a placeholder
            except OSError as e:
                try:
                    os.rmdir(item)
                except OSError as e:
                    pass
        return

    def revert_nocopy_renaming(self, verbose=True):
        """
        Description:
        Reverts the naming (adding of the _NC tag)


        Usage:

        Params:

        """
        reverse_rename_dict = self.scan_dirs(sacredtexts=self.sacredtexts)
        to_rename_back = [folder for folder in reverse_rename_dict.keys()
                          if '_DEL' in folder and '_NC']
        for directory_to_rename in to_rename_back:
            reverted_name = directory_to_rename.replace('_DEL', '').replace('_NC', '')
            os.replace(directory_to_rename, reverted_name)
            if verbose:
                print(f'Renamed {directory_to_rename} to {reverted_name}.')
        return

    def full_clean_job(self):

        """
        Perform the whole cleaning of the service
        """
        # if '_NC' in ____ or '_DEL' in ___:
        # print that a previous usage of this was detected
        # self.rename()
        # self.delete()

        return
