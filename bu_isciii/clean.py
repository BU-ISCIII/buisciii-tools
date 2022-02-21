#!/usr/bin/env python
'''
=============================================================
HEADER
=============================================================
INSTITUTION: BU-ISCIII
AUTHOR: Guillermo J. Gorines Cordero
MAIL: guillermo.gorines@urjc.es
VERSION: 1.0
CREATED: 21-2-2022
REVISED: 21-2-2022
REVISED BY:
DESCRIPTION:
OPTIONS:

USAGE:

REQUIREMENTS:

TO DO:
    -INIT: where to find the needed values
    -PATH: where to be placed
        -BASE_DIRECTORY: where is it? How do we know where it is?


    -NAMING: let's be honest, those are terrible
================================================================
END_OF_HEADER
================================================================
'''
# Generic imports
import sys
import os

# Local imports

class CleanUp(self):
    def __init__(self,resolution_name):
        # access the api/the json/the whatever with the service name to obtain
        
        self.resolution_name = resolution_name
        self.base_directory =
        self.delete =
        self.nocopy =


    def show_removable_dirs(self, to_stdout = True):
        """
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

    def show_nocopy_dirs(self, to_stdout = True):
        """
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

    def delete(self, sacredtexts=['lablog','logs'], verbose = True):
        """
        Remove the files that must be deleted for the delivery of the service
        Their contains, except for the lablog file, and the logs dir, will be
        deleted

        Usage:
            object.delete()

        Params:
            sacreditems [list]: names (str) of the files that shall not be deleted.

        """

        for root, dirs, _ in os.walk():
            # if there's at least one dir
            if len(dirs) > 0:
                for directory in dirs:
                    if directory in self.delete:
                        # generate the directory path:
                        to_be_deleted_dir = os.path.join(root,directory)
                        
                        for content in os.listdir(to_be_deleted_dir):

                            if content not in sacredtexts:
                                
                                file_to_be_deleted = os.path.join(to_be_deleted_dir,content)
                                os.remove(file_to_be_deleted)

                                if verbose:
                                    print(f'Removed: {file_to_be_deleted}.')
                        
                        new_name = to_be_deleted_dir + '_DEL'
                        os.replace(to_be_deleted_dir, new_name)
        return

    def rename(self):
        """
        Rename the files and directories with a _NC so it is not copied into the
        delivery system.

        Usage:

        Params:

        """
        for _, dirs, folders in os.walk():

        for old_name in self.nocopy:
            new_name = old_name + '_NC'
            os.rename(old_name, new_name)

        return

    def revert_renaming(self, verbose = True):
        """
        Reverts the naming (adding of the _NC tag)
        """
        for root, dirs, _ in os.walk():
            # if there's at least one dir
            if len(dirs) > 0:
                for directory in dirs:
                    if '_NC' in directory:
                        nc_path = os.path.join(root,directory)

                        reverted_name = directory - '_NC'
                        reverted_path = os.path.join(root,reverted_name)
                        
                        os.replace(nc_path, reverted_path)

                        if verbose:
                            print(f"Reverted {directory} to {reverted_name}")
        return 

    def revert_delete_renaming(self, verbose = True):
        """

        """
        for root, dirs, _ in os.walk():
            if len(dirs) > 0:
                if '_DEL' in directory:
                    del_path = os.path.join()


        return 


    def full_clean_job(self):     
        
        """
        Perform the whole cleaning of the service 
        """

        if '_NC' in ____ or '_DEL' in ___:

            # print that a previous usage of this was detected

        

        self.rename()
        self.delete()

        return 