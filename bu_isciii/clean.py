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
================================================================
END_OF_HEADER
================================================================
'''
# Generic imports
import sys
import os

# Local imports

class CleanUp(self):
    def __init__(self,):
        # access the api/the json/the whatever with the service name to obtain
        self.removes = 
        self.renames = 


    def show_removable_dirs(self, to_stdout = True):
        """
        Print or return the list of objects that must be deleted in this service
        
        Usage: 
            object.show_removable_dirs(to_stdout = [BOOL])

        Params:
            to_stdout [BOOL]: if True, print the list. If False, return the list.
        """
        if to_stdout:
            print(self.removes)
            return
        else:
            return self.removes
        
    def show_renameable_dirs(self, to_stdout = True):
        """
        Print or return the list of objects that must be renamed in this service
        
        Usage: 
            object.show_renameables_dirs(to_stdout = [BOOL])

        Params:
            to_stdout [BOOL]: if True, print the list. If False, return the list.
        """

        if to_stdout:
            print(self.renames)
            return
        else:
            return self.renames

    def delete_removes(self, sacreditems=["lablog","logs"],verbose = True):
        """
        Remove the files that must be deleted for the delivery of the service
        Their contains, except for the lablog file, and the logs dir, will be
        deleted
        
        Usage:
            object.delete_removes()
        
        Params:
            sacreditems [list]: names (str) of the files that shall not be deleted.

        """

        for item_to_remove in self.removes:
            for content in os.listdir(item_to_remove):
                if content not in sacreditems:
                    os.remove(content)
                    if verbose:
                        print(f'Removed: {content}')
                        


    def rename_renamables(self):
        """
        Rename the files and directories with a _NC so it is not copied into the
        delivery system.

        Usage:
        
        Params:

        """
        
        for old_name in self.renames:
            new_name = old_name + '_NC'
            os.rename(old_name, new_name)




    def full_clean_job(self):

