#!/usr/bin/env python
#   sftp_autoclean.py
#
#   Gaol: automatically remove service from sftp after X days after the last update/access  
#       Sub goals:
#           1. add && custom stderr.prints + colors
#           2. Get sftp service metadata from jsons
#           3. Mark services that are stored for long period-time
#           4. Provide a log-completition file. 
#           5. linting -- pep8 & black

# import
import os
import re
import sys
import logging

import shutil
import rich

from datetime import datetime, timedelta

# local import
import bu_isciii 
import bu_isciii.utils

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)

# TODO: add to utils.py?
def timestamp_converter(timestamp):
    date_formated = datetime.fromtimestamp(timestamp)
    return date_formated

class LastMofdificationFinder:
    '''
    Identifies the lates modification in a directory
    '''
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

class AutoremoveSftpService:
    '''
    Identifies service's stored in an sftp directory 
    and remove those that have not been updated/modified
    within 14 days
    '''
    def __init__(self, path=None, window=14):
        # Parse input path
        if path is None:
            use_default = bu_isciii.utils.prompt_yn_question("Use default path?: ")
            if use_default:
                # TODO: add import json-api sftp  path
                #self.path = bu_isciii.config_json.ConfigJson().get_configuration("PATHTO")
                print("yes")
                sys.exit()
            else:                             
                self.path = bu_isciii.utils.prompt_path(msg="Directory where the sftp site is allocated:")
        else:
            self.path = path
        
        # Get window margin to determine old services
        self.window = timedelta(days=window)

    # TODO: modify this. PR to make this method reusable outside the class
    def check_path_exists(self):
        # if the folder path is not found, then bye
        if not os.path.exists(self.path):
            print( # TODO: replace with stderr.print
                "[red] ERROR: It seems like finding the correct path is beneath me. I apologise. The path: %s does not exitst. Exiting.."
                % self.path
            )
            sys.exit()
        else: 
            return True
    
    # Uses regex to identify sftp-services & gets their lates modification
    def get_sftp_services(self):
        self.sftp_services = {} # {sftp-service_path : last_update}
        service_pattern = r'^[SRV][A-Z]+[0-9]+_\d{8}_[A-Z0-9]+_[a-zA-Z]+(?:\.[a-zA-Z]+)?_[a-zA-Z]$'
        
        for root, dirs, files in os.walk(self.path):
            for dir_name in dirs:
                match = re.match(service_pattern, dir_name)
                if match:
                    sftp_service_fullPath = os.path.join(root,dir_name)
                    
                    # Get sftp-service last modification
                    service_finder = LastMofdificationFinder(sftp_service_fullPath)
                    service_last_modification = service_finder.find_last_modification()
                    self.sftp_services[sftp_service_fullPath] = service_last_modification
        if len(self.sftp_services) == 0:
            sys.exit(f"No services found in {self.path}")
    
    # Mark services older than $window    
    def mark_toDelete(self):
        self.marked_services = []

        for key, value in self.sftp_services.items():
            if datetime.now() - value > self.window:
                self.marked_services.append(key)
    
    # Delete marked services 
    def remove_oldservice(self):
        if len(self.marked_services) == 0:
            sys.exit(f"sftp-site up to date. There are no services  older than {self.window} days. Skiping autoclean_sftp...")
        else:
            service_elements='\n'.join(self.marked_services)
            print(f"The following services are going to be deleted from the sftp:\n{service_elements}") # replace with isciii std err
            confirm_sftp_delete = bu_isciii.utils.prompt_yn_question("Are you sure?: ")
            if confirm_sftp_delete:
                for service in self.marked_services:
                    try:
                        print(f"Deleting service: {service}") # replace with isciii std err
                        #shutil.rmtree(os.path.join(self.path, sftp_folder))
                    
                    except OSError as o:
                        print(f"[ERROR] Cannot delete service folder {service}: {os.path.join(self.path, service)}") # replace with isciii std err & import colors
    
    def handle_autoclean_sftp(self):
        self.check_path_exists()
        self.get_sftp_services()
        self.mark_toDelete()
        self.remove_oldservice()