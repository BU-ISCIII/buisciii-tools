#!/usr/bin/env python

# Generic imports
import sys
import os
import logging
import filecmp
import shutil
import sysrsync
import rich
import calendar
import hashlib
import tarfile
from math import pow
from datetime import date

# Local imports
import bu_isciii
import bu_isciii.utils
import bu_isciii.config_json
import bu_isciii.drylab_api

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)

def ask_date(previous_date=None):
    """
    Ask the year, then the month, then the day of the month
    This choice is always dependent on wether the date is or not available
    return a 3 items list
    If given a "previous_date" argument, always check that the date is posterior
    "previous_date" format is the same as this functions output:
    [year [str], chosen_month_number [str], day [str]]
    Stored like this so that its easier to manage later
    """
    
    lower_limit_year = 2010 if previous_date is None else int(previous_date[0]) 

    # Range: lower_limit_year - current year
    year = bu_isciii.utils.prompt_year(lower_limit=lower_limit_year,
                                       upper_limit=date.today().year)

    # Limit the list to the current month if year = current year
    # This could be a one-liner:
    # month_list = [[num, month] for num, month in enumerate(month_name)][1:] if year < date.today().year else month_list = [[num, month] for num, month in enumerate(month_name)][1:date.today().month+1]
    # I found it easier the following way:
    if year < date.today().year:
        month_list = [[num, month] for num, month in enumerate(calendar.month_name)][1:]
    else:
        month_list = [[num, month] for num, month in enumerate(calendar.month_name)][1:date.today().month+1]

    # If there is a previous date
    # and year is the same as before, limit the quantity of months
    if previous_date is not None and year == int(previous_date[0]):
        month_list = month_list[int(previous_date[1])-1:]
        
    chosen_month_number, chosen_month_name = bu_isciii.utils.prompt_selection(f"Choose the month of {year} from which start counting",
                                             [f"Month {num:02d}: {month}" for num, month in month_list]).replace("Month","").strip().split(": ")

    # For the day, use "calendar":
    # calendar.month(year, month) returns a string with the calendar
    # Use replace to move the "\n"
    # Use split " " to generate a list
    # Use filter to remove empty strings that may appear
    # Do not get the 9 first elements bc they are:
    # "Month", "Year", "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"

    day_list = list(filter(None, calendar.month(year, int(chosen_month_number)).replace("\n"," ").split(" ")))[9:]

    # if current month and day, limit the options to the current day
    if year == date.today().year and int(chosen_month_number) == date.today().month:
        day_list = day_list[:date.today().day]
    
    # if previous date  & same year & same month, limit days
    if previous_date is not None and year == int(previous_date[0]) and chosen_month_number == previous_date[1]:
        day_list = day_list[int(previous_date[2])-1:]

    # from the list, get the first and last item as limits for the function
    day = bu_isciii.utils.prompt_day(lower_limit=int(day_list[0]),
                                     upper_limit=int(day_list[-1]))


    return [str(year), str(chosen_month_number), str(day)]

# function to compare directories (archived and non-archived)
def dir_comparison(dir1, dir2):
    """
    Generates a filecmp.dircmp comparison object
    RECURSIVELY, checks each of the dirs to check if
    they are the same.

    Heavily based on:
    https://stackoverflow.com/questions/4187564/recursively-compare-two-directories-to-ensure-they-have-the-same-files-and-subdi
    """
    comparison = filecmp.dircmp(dir1, dir2)
    if (
        comparison.left_only
        or comparison.right_only
        or comparison.diff_files
        or comparison.funny_files
    ):
        return False
    for subdir in comparison.common_dirs:
        if not dir_comparison(os.path.join(dir1, subdir), os.path.join(dir2, subdir)):
            return False
    return True


def get_service_paths(conf, ser_type, service):
    """
    Given a service, a conf and a type,
    get the path it would have in the
    archive, and outside of it

    NOTE: for some services, the 'profileClassificationArea' is None, and the os.path.join may fail
    
    """
    print(f"archived_path : {conf['archived_path']}")
    print(f"ser_type : {ser_type}")
    print(f"profilecenter: {service['serviceUserId']['profile']['profileCenter']}")
    print(f"area: {service['serviceUserId']['profile']['profileClassificationArea'].lower()}")

    # Path in archive
    archived = os.path.join(
        conf["archived_path"],
        ser_type,
        service["serviceUserId"]["profile"]["profileCenter"],
        service["serviceUserId"]["profile"]["profileClassificationArea"].lower(),
    )

    # Path out of archive
    non_archived = os.path.join(
        conf["data_path"],
        ser_type,
        service["serviceUserId"]["profile"]["profileCenter"],
        service["serviceUserId"]["profile"]["profileClassificationArea"].lower(),
    )

    return archived, non_archived


def get_dir_size(path):
    """
    Get the size of a given directory
    """
    size = 0

    for path, dirs, files in os.walk(path):
        for f in files:
            size += os.path.getsize(os.path.join(path, file))

    return size


def targz_dir(tar_name, directory):
    """
    Generate a tar gz file with the contents of a directory 
    """
    try:
        with tarfile.open(tar_name, "w:gz") as out_tar:
            out_tar.add(directory)
        return True
    except Exception as e:
        # Have to check which error to expect
        return False


def get_md5(file):
    """
    Given a file, open it and digest to get the md5
    NOTE: might be troublesome when infile is too big
    Based on: 
    https://www.quickprogrammingtips.com/python/how-to-calculate-md5-hash-of-a-file-in-python.html
    """
    with open(file,"rb") as infile:
        infile = infile.read()
        file_md5 = hashlib.md5(infile).hexdigest()

    return file_md5


class Archive:
    """
    Class to perform the storage and retrieval
    of a service
    """

    def __init__(self, resolution_id=None, ser_type=None, api_token=None,option=None):
        # resolution_id = Nombre de la resolución
        # ser_type = services_and_colaborations // research
        # option = archive/retrieve

        self.resolution_id = resolution_id
        self.type = ser_type
        self.option = option
        
        """
        ANCHOR CODE: when "year" option was removed, this chunk became deprecated 
        # assumption: year and no resolution_id >>> Batch management
        self.quantity = (
            "Batch" 
            if self.year is not None and self.resolution_id is None 
            else None
        )
        # assumption: resolution_id and no year >>> Single service management
        self.quantity = (
            "Single service"
            if self.resolution_id is not None and self.year is None
            else None
        )
        """

        self.quantity = bu_isciii.utils.prompt_selection(
            "Working with a batch, or a single resolution?",
            ["Batch", "Single service"],
        )

        # Get configuration params from configuration.json
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("archive")
        
        # Get data to connect to the api
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")

        # Initiate API
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )

        if self.quantity == "Batch":

            stderr.print("Please state the initial date for filtering")
            self.date_from = ask_date()

            stderr.print("Please state the final date for filtering (must be posterior or identical to the initial date)")
            self.date_until = ask_date(previous_date=self.date_from)
            
            stderr.print(f"Asking our trusty API about resolutions between: {'-'.join(self.date_from)} and {'-'.join(self.date_until)}")

            # Ask the API for services within the range
            # safe is False, so instead of exiting, an error code will be returned
            services_batch = rest_api.get_request(
                            request_info = "services",
                            parameter1 = "date_from", 
                            value1 = "-".join(self.date_from),
                            parameter2 = "date_until",
                            value2 = "-".join(self.date_until),
                            safe = False,
                        )

            # if int (if error code), must be only bc status > 200
            # Check drylab_api.get_request
            if isinstance(services_batch, int):
                stderr.print(f"No services were found in the interval {'-'.join(self.date_from)} and {'-'.join(self.date_until)}. Connection seemed right though!")
                sys.exit()
            else: 
                stderr.print(f"Found {len(self.services_to_move)} services in the interval {'-'.join(self.date_from)} and {'-'.join(self.date_until)}!")
            
            # Get individual serviceFullData for each data
            # I dont really like hardcoding the .1 in the f-string but I doubt I have a choice honestly
            self.services_to_move = [rest_api.get_request(
                request_info = "serviceFullData",
                parameter1= "resolution",
                value1 = f"{service_batch['serviceRequestNumber']}.1",
                ) for service_batch in services_batch]
            
            # services_batch does not seem useful from now on, so delete it from memory
            del services_batch

        elif self.quantity == "Single service" and self.resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
            
            stderr.print(f"Asking our trusty API about resolution: {self.resolution_id}")

            # Hold the results in a list so it can be accessed just like in the batch
            self.services_to_move = [rest_api.get_request(
                    request_info = "serviceFullData", 
                    parameter1 = "resolution",
                    value1 = self.resolution_id,
                    safe = False
                )]
        
            if isinstance(services_batch[0], int):
                stderr.print(f"No services named {self.resolution_id} were found. Connection seemed right though!")
                sys.exit()
        
        # Get configuration params from configuration.json
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("archive")

        # Get data to connect to the api
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration(
            "xtutatis_api_settings"
        )

        # Obtain info from iSkyLIMS api with the conf_api info

        print(self.services_to_move)
            
        # Calculate size of the directories (already in GB)
        """
        stderr.print(
            "Calculating total size of the directories to be filed.",
            highlight=False,
        )
        self.total_size = sum([get_dir_size(directory) for directory in self.services_to_move]) * 9.31 * pow(10,-9)
        """

        if self.type is None:
            stderr.print(f"Working with a service, or a research resolution?")
            self.type = bu_isciii.utils.prompt_selection(
                "Type",
                ["services_and_colaborations", "research"],
            )

        if option is None:
            stderr.print(f"Willing to archive, or retrieve a resolution?")
            self.option = bu_isciii.utils.prompt_selection(
                "Options",
                ["archive", "retrieve"],
            )
        
    def archive(self):
        """
        Archive services in selected year and month
        """      
        
        # with a total size of {self.total_size:.2f} GB.
        if (bu_isciii.utils.prompt_selection(
            f"The selection you want to file consists of {len(self.services_to_move)} services. Continue?",
            ["Yes, continue", "Hold up"])) == "Yes, continue":

            for service in self.services_to_move:
                # stderr.print(service["servicFolderName"])

                dest, source = get_service_paths(self.conf, self.type, service)

                try:
                    sysrsync.run(
                        source=source,
                        destination=dest,
                        options=self.conf["options"],
                        sync_source_contents=False,
                    )
                    stderr.print(
                        "[green] Data copied successfully to its destiny archive folder",
                        highlight=False,
                    )
                except OSError as e:
                    stderr.print(
                        "[red] ERROR: Data could not be copied to its destiny archive folder.",
                        highlight=False,
                    )
                    log.error(
                        f"Directory {self.source} could not be archived to {self.dest}.\
                            Reason: {e}"
                    )
            return

    def retrieve_from_archive(self):
        """
        Copy a service back from archive
        """

        for service in self.services_to_move:
            # stderr.print(service["servicFolderName"])

            print(f"archived_path : {self.conf['archived_path']}")
            print(f"type: {self.type}")
            print(f"profileCenter: {service['serviceUserId']['profile']['profileCenter']}")
            print(f"Area: {service['serviceUserId']['profile']['profileClassificationArea'].lower()}")

            source = os.path.join(
                self.conf["archived_path"],
                self.type,
                service["serviceUserId"]["profile"]["profileCenter"],
                service["serviceUserId"]["profile"]["profileClassificationArea"].lower(),
            )

            dest = os.path.join(
                self.conf["data_path"],
                self.type,
                service["serviceUserId"]["profile"]["profileCenter"],
                service["serviceUserId"]["profile"]["profileClassificationArea"].lower(),
            )

            try:
                sysrsync.run(
                    source=source,
                    destination=dest,
                    options=self.conf["options"],
                    sync_source_contents=False,
                )
                stderr.print(
                    "[green] Data retrieved successfully from its archive folder.",
                    highlight=False,
                )
            except OSError as e:
                stderr.print(
                    "[red] ERROR: Data could not be retrieved from its archive folder.",
                    highlight=False,
                )
                log.error(
                    f"[red] ERROR: Directory {self.source} could not be archived to {self.dest}.\
                    Reason: {e}"
                )

        return

    def delete_origin(self):
        """
        Delete the origin of the previous archive or retrieval
        """
        for service in self.services_to_move:
            if self.option == "archive":
                dest, source = get_service_paths(self.conf, self.type, service)
            elif self.option == "retrieve":
                source, dest = get_service_paths(self.conf, self.type, service)

            if not dir_comparison(source, dest):
                err_msg = f"[red]ERROR: Cannot delete {source} because it does not match {dest}"
                stderr.print(err_msg)
                log.error(err_msg)
            else:
                shutil.rmtree(source)

        return

    def handle_archive(self):
        """
        Handle archive class options
        """
        if self.option == "archive":
            self.archive()
        if self.option == "retrieve":
            self.retrieve_from_archive()
        return
