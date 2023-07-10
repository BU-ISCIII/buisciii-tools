#!/usr/bin/env python
#   sftp_autoclean.py
#
#   Gaol: automatically remove service from sftp after X days after the last update/access  
#       Sub goals:
#           1. Get user confirmation --> yes/no [prompt]
#           2. Agument -p [path] or default [resolution.id ftp path]
#           1. Get sftp service metadata from jsons
#           2. Get last access/modification date (this may be checked not only in the parent floder but also in all childrens)   
#           3. Implement logic. I condition is met then, apply auto-cleanup
#           4. Add a prortection property in order to avoid cleaning files that will be store in sftp for long-period time.
#           5. Provide a log-completition file. 
#           6. linting -- pep8 & black

# import
import os
import shutil
import sys
import logging
import rich
import questionary
from datetime import datetime, timedelta

# import locals
#import buisciii.utils

# add loggin and colors

# create class

# =================================================================
# Backbone and utils
# =================================================================

# temp cp from utils
def prompt_path(msg):
    source = questionary.path(msg).unsafe_ask()
    return source

def prompt_yn_question(msg):
    confirmation = questionary.confirm(msg).unsafe_ask()
    return confirmation

# New functions(mv to utils)
def timestamp_converter(timestamp): # import datetime
    date_formated = datetime.fromtimestamp(timestamp)
    return date_formated

def last_updated_file(datetime_list):
    latest_date = max(datetime_list)
    return latest_date

class LastMofdificationFinder:
    def __init__(self, path):
        self.path = path
        self.last_modified_time = 0
    
    def find_last_modification(self):
        self.get_last_modified(self.path)
        return timestamp_converter(self.last_modified_time)

    def get_last_modified(self, directory):
        last_modified_time = os.path.getmtime(directory)

        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                file_modified_time = os.path.getmtime(file_path)
                if file_modified_time > last_modified_time:
                        last_modified_time = file_modified_time

        if last_modified_time > self.last_modified_time:
                    self.last_modified_time = last_modified_time

# TODO: add corner case: service list to be celaned, empty
# TODO: If check_path_exist becomes more flexible, allow inheritance AutoremoveSftpService(bu_isciii.clean.CleanUp) + super()
class AutoremoveSftpService:
    def __init__(self, path):
        if path is None:
            # TODO: Replace with stderr() once implemented
            print("Directory where the sftp site is allocated")
            # TODO: Replace with bu_isciii.utils.prompt_path() once implemented
            self.path = prompt_path(msg="Path")
        else:
            self.path = path
       
    # TODO: modify this. PR to make this method reusable outside the class
    def check_path_exists(self):
        # if the folder path is not found, then bye
        if not os.path.exists(self.path):
            print( # TODO: replace with stderr.print
                "[red] ERROR: It seems like finding the correct path is beneath me. I apologise. The path: %s does not exitst. Exiting.."
                % self.path
            )
            sys.exit()

    def remove_service(self): # prompt thing
        service_elements='\n'.join(self.services)
        print(f"The following services will be deleted:\n{service_elements}") # replace with isciii std err
        confirm_sftp_delete = prompt_yn_question(
            "Are you sure?:"
            )
        if confirm_sftp_delete:
            for sftp_folder in self.services:
                try:
                    print(f"Deleting service {sftp_folder}: {os.path.join(self.path, sftp_folder)}") # replace with isciii std err
                    #shutil.rmtree(os.path.join(self.path, sftp_folder))
                    
                except OSError as o:
                    print(f"[ERROR] Cannot delete service folder {sftp_folder}: {os.path.join(self.path, sftp_folder)}") # replace with isciii std err
    
sftp_site_autoclean = AutoremoveSftpService(None, True)
sftp_site_autoclean.check_path_exists()