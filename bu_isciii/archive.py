#!/usr/bin/env python

# Generic imports
import sys
import os
import logging
import shutil
import sysrsync
import rich
import calendar
import hashlib
import tarfile
import datetime
from math import pow

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


def ask_date(previous_date=None, posterior_date=None, initial_year=2010):
    """
    Ask the year, then the month, then the day of the month
    This choice is always dependent on wether the date is or not available
    return a 3 items list
    If given a "previous_date" argument, always check that the date is posterior
    "previous_date" format is the same as this functions output:
    [year [str], chosen_month_number [str], day [str]]
    Stored like this so that its easier to manage later
    """

    lower_limit_year = initial_year if previous_date is None else previous_date.year

    # Range: lower_limit_year - current year
    year = bu_isciii.utils.prompt_year(lower_limit=lower_limit_year, upper_limit=datetime.date.today().year)

    # Limit the list to the current month if year = current year
    # This could be a one-liner:
    # month_list = [[num, month] for num, month in enumerate(month_name)][1:] if year < date.today().year else month_list = [[num, month] for num, month in enumerate(month_name)][1:date.today().month+1]
    # I found it easier the following way:
    if year < datetime.date.today().year:
        month_list = [[num, month] for num, month in enumerate(calendar.month_name)][1:]
    else:
        month_list = [[num, month] for num, month in enumerate(calendar.month_name)][1 : datetime.date.today().month + 1]

    # If there is a previous date
    # and year is the same as before, limit the quantity of months
    if previous_date is not None and year == previous_date.year:
        month_list = month_list[previous_date.month - 1 :]

    chosen_month_number, chosen_month_name = (
        bu_isciii.utils.prompt_selection(
            f"Choose the month of {year} from which start counting",
            [f"Month {num:02d}: {month}" for num, month in month_list],
        )
        .replace("Month", "")
        .strip()
        .split(": ")
    )
    # For the day, use "calendar":
    # calendar.month(year, month) returns a string with the calendar
    # Use replace to move the "\n"
    # Use split " " to generate a list
    # Use filter to remove empty strings that may appear
    # Do not get the 9 first elements bc they are:
    # "Month", "Year", "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"

    day_list = list(filter(None,calendar.month(year, int(chosen_month_number)).replace("\n", " ").split(" "),))[9:]

    # if current month and day, limit the options to the current day
    if (
        year == datetime.date.today().year
        and int(chosen_month_number) == datetime.date.today().month
    ):
        day_list = day_list[: datetime.date.today().day]

    # if previous date  & same year & same month, limit days
    if (previous_date is not None and year == previous_date.year and chosen_month_number == previous_date.month):
        day_list = day_list[previous_date.day - 1 :]

    # from the list, get the first and last item as limits for the function
    day = bu_isciii.utils.prompt_day(lower_limit=int(day_list[0]), upper_limit=int(day_list[-1]))

    return datetime.date(int(year), int(chosen_month_number), int(day))


def validate_date(date_previous, date_posterior):

        

    return


def get_service_paths(conf, ser_type, service):
    """
    Given a service, a conf and a type,
    get the path it would have in the
    archive, and outside of it

    NOTE: for some services, the 'profileClassificationArea' is None, and the os.path.join may fail
    """
    center = (
        service["serviceUserId"]["profile"]["profileClassificationArea"].lower()
        if isinstance(
            service["serviceUserId"]["profile"]["profileClassificationArea"], str
        )
        else ""
    )

    # print(service)
    # print(f"data_path: {conf['data_path']}")
    # print(f"archived_path : {conf['archived_path']}")
    # print(f"ser_type : {ser_type}")
    # print(f"profilecenter: {service['serviceUserId']['profile']['profileCenter']}")
    # print(f"clasfification area: {center}")

    # Path in archive
    archived_path = os.path.join(
        conf["archived_path"],
        ser_type,
        service["serviceUserId"]["profile"]["profileCenter"],
        center,
        service["serviceRequestNumber"],
    )

    # Path out of archive
    non_archived_path = os.path.join(
        conf["data_path"],
        ser_type,
        service["serviceUserId"]["profile"]["profileCenter"],
        center,
        service["serviceRequestNumber"],
    )

    return archived_path, non_archived_path


def get_dir_size(path):
    """
    Get the size in bytes of a given directory
    """
    size = 0

    for path, dirs, files in os.walk(path):
        for file in files:
            size += os.path.getsize(os.path.join(path, file))

    return size


def targz_dir(tar_name, directory):
    """
    Generate a tar gz file with the contents of a directory
    """
    with tarfile.open(tar_name, "w:gz") as out_tar:
        out_tar.add(directory, arcname=os.path.basename(directory))
    return True


def uncompress_targz_directory(tar_name, directory):
    """
    Untar GZ file
    """
    with tarfile.open(tar_name) as out_tar:
        out_tar.extractall("/".join(directory.split("/")[:-1]))
    return


def get_md5(file):
    """
    Given a file, open it and digest to get the md5
    NOTE: might be troublesome when infile is too big
    Based on:
    https://www.quickprogrammingtips.com/python/how-to-calculate-md5-hash-of-a-file-in-python.html
    """
    with open(file, "rb") as infile:
        infile = infile.read()
        file_md5 = hashlib.md5(infile).hexdigest()

    return file_md5


def generate_tsv_table(indict, chosen_filename):

    """
    Create a csv file containing the info for each service
    """

    if os.path.exists(chosen_filename):
        new_filename = filename.split(".")[0] + ".tsv"
        stderr.print(f"A tsv file named {chosen_filename} has already been found. Changing name to {new_filename}.")
        log.info(f"A tsv file named {chosen_filename} has already been found. Name changed to {new_filename}".)
    else:
        stderr.print(f"Generating TSV table to: {chosen_filename}")
        log.info(f"STARTING: Generation of TSV table to: {chosen_filename}")
        filename = chosen_filename

    with open(filename, "w") as infile:

        csv_dict =  {
                        "Service ID" : None,
                        "Found on iSkyLIMS": None,
                        "Delivery date": None,
                        "Path in archive": None,
                        "Found on archive": None,
                        "Uncompressed size in archive": None,
                        "Compressed size in archive": None,
                        "Compressed md5 in archive": None,
                        "Path in data directory": None,
                        "Found on data directory": None,
                        "Uncompressed size in data directory": None,
                        "Compressed size in data directory": None,
                        "Compressed md5 in data dir": None,
                        "Compressing process": None,
                        "Moving process": None,
                        "Uncompressing process": None,
                        "Deletion process": None,
                    }
                
        infile.write("\t".join(list(csv_dict.keys())))
        
        for service in indict.keys():
            csv_dict["Service ID"] = service
            csv_dict["Found on iSkyLIMS"] = "Found on iSkyLIMS" if indict[service]["found_in_system"] is True else "NOT found on iSkyLIMS"
            csv_dict["Delivery date"] = "" 

            # Fields for archive
            csv_dict["Path in archive"] = indict[service]["archived_path"] if indict[service]["archived_path"] is not None else "Archived path could not be generated"
            csv_dict["Found in archive"] = "Yes" if "Archive" in indict[service]["found"] else "Not found in archive"
            csv_dict["Uncompressed size in archive"] = indict[service]["archived_size"] if indict[service]["archived_size"] != 0 else "Not calculated"
            csv_dict["Compressed size in archive"] = indict[service]["archived_compressed_size"] if indict[service]["archived_compressed_size"] != 0 else "Not calculated"
            csv_dict["Compressed md5 in archive"] = indict[service]["md5_non_archived"] if indict[service]["md5_non_archived"] is not None else "Not obtained"
            
            # Fields for data directory
            csv_dict["Path in data directory"] = indict[service]["non_archived_path"] if indict[service]["non_archived_path"] is not None else "Data path could not be generated"
            csv_dict["Found on data directory"] = "Yes" if "Data dir" in indict[service]["found"] else "Not found in data dir"
            csv_dict["Compressed size in data directory"] = indict[service]["non_archived_size"] if indict[service]["non_archived_size"] != 0 else "Not calculated"
            csv_dict["Uncompressed size in data directory"] = indict[service]["non_archived_compressed_size"] if indict[service]["non_archived_compressed_size"] != 0 else "Not calculated"
            csv_dict["Compressed md5 in data dir"] = indict[service]["md5_non_archived"] if indict[service]["md5_non_archived"] is not None else "Not obtained"
            
            # Fields for processes
            csv_dict["Compressing process"] = indict[service]["compressed"]
            csv_dict["Moving process"] = indict[service]["moved"]
            csv_dict["Uncompressing process"] = indict[service]["uncompressed"]
            csv_dict["Deletion process"] = indict[service]["deleted"]

            infile.write("\t".join(list(indict.values())))
            stderr.print(f"Added service {service} to the TSV file")
            log.info(f"Service {service} added successfully to TSV file named {filename}")
    log.info(f"FINISHED: Generation of TSV table to: {filename}")

    return

class Archive:
    """
    Class to perform the storage and retrieval
    of a service
    """

    def __init__(self, service_id=None, ser_type=None, option=None, api_pass=None, skipt_prompts=False, initial_date=None, final_date=None):
        # resolution_id = resolution name (SRVCNM656)
        # ser_type = services_and_colaborations // research
        # option = archive/retrieve

        dictionary_template = {
                "found_in_system": "",
                "delivery_date": "",
                "archived_path": "",
                "non_archived_path": "",
                "archived_size": int(),
                "archived_compressed_size" : int(),
                "non_archived_size": int(),
                "non_archived_compressed_size" : int(),
                "found": [],
                "md5_non_archived" : "",
                "md5_archived" : "",
                "compressed": "No compression performed",
                "moved": "No movement performed",
                "uncompressed": "No uncompression performed",
                "deleted": "No deletion performed",
                "error_status": "No errors detected",
            }

        if ((initial_date is None) and (final_date is not None)) or ((initial_date is not None) and (final_date is None)):
            stderr.print(f"Initial date was {("not" if initial_date is None else "")} set, but Final date was {("not" if final_date is None else "")}. Please provide both!")
            sys.exit() 
        
        if ((initial_date is not None) and (final_date is not None) and (service_id is not None)):
            stderr.print("Both a date and a service ID have been chosen. Which one would you like to keep?")
            prompt_response = bu_isciii.utils.prompt_selection("Date or Service ID?",["Search by date", "Search by ID"],)
            if (prompt_response) == "Search by date":
                initial_date = None
                final_date = None
            else:
                service_id = None

        self.skip_prompts = skip_prompts
        self.type = ser_type
        self.option = option

        # deepcopy can be used here
        # import copy 
        #  service_id : copy.deepcopy(dictionary_template)
        self.services = {
            service_id: { key : value for key, value in dictionary_template.items() }
        } if service_id is not None else dict()

        # LOG: called the archive repository
        log.info("Activated archive module of the bu-isciii tools")
        
        # Get configuration params from configuration.json
        # Get data to connect to the API
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("archive")
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")

        # Initiate API
        rest_api = bu_isciii.drylab_api.RestServiceApi(conf_api["server"], conf_api["api_url"],api_pass,)

        if self.type is None or self.type not in ["service_and_colaborations", "research"]:
            stderr.print("Working with a service, or a research resolution?")
            self.type = bu_isciii.utils.prompt_selection("Type",["services_and_colaborations", "research"],)

        log.info(f"Service type chosen: {self.type}")

        prompt_response = bu_isciii.utils.prompt_selection("Search services by date, or by resolution ID?",["Search by date", "Resolution ID"],)
        if (prompt_response == "Search by date"):
            log.info(f"Services chosen by: date")
            
            stderr.print("Please state the initial date for filtering")
            self.date_from = ask_date()
            stderr.print("Please state the final date for filtering (must be posterior or identical to the initial date)")
            self.date_until = ask_date(previous_date=self.date_from)

            log.info(f"Starting date: {self.date_from} (chosen through prompt)")
            log.info(f"Ending date: {self.date_until} (chosen through prompt)")
            stderr.print(f"Asking our trusty API about resolutions between: {self.date_from} and {self.date_until}")

            try:
                for service in rest_api.get_request(request_info="services", safe=False, state="delivered", date_from=str(self.date_from), date_until=str(self.date_until),):
                    self.services[service["serviceRequestNumber"]] = { key : value for key, value in dictionary_template.items() }
                    self.services[service["serviceRequestNumber"]]["found_in_system"] = True
                    self.services[service["serviceRequestNumber"]]["delivery_date"] = service["serviceOnDeliveredDate"] 

                log.info(f"Services found in the time interval: {len(self.services)}")
                log.info(f"Names of the services found in said interval: {','.join([service for service in self.services.keys()])}")
                
            except TypeError:
                stderr.print("Could not connect to the API (wrong password?)", style="red")
                log.error("Connection to the API was not successful. Possible reasons: wrong API password, bad connection.")
                sys.exit(1)
        else:
            log.info(f"Services chosen by: ServiceID")
            if len(self.services.keys()) == 0:
                new_service = bu_isciii.utils.prompt_service_id()
                self.services = {new_service: {key : value for key, value in dictionary_template.items()}}
                log.info(f"Chosen service: {new_service} (chosen through prompt)")
   
            # Ask if more services will be chosen
            while True:
                prompt_response = bu_isciii.utils.prompt_selection("Would you like to add any other service?",["Add more services", "Do not add more services"],)
                if (prompt_response == "Do not add more services"):
                    break
                else:
                    new_service = bu_isciii.utils.prompt_service_id()
                    self.services[new_service] = {key : value for key, value in dictionary_template.items()}
                    log.info(f"Chosen service: {new_service} (chosen through prompt)")

        stderr.print(f"Asking our trusty API about services: {', '.join([service for service in self.services.keys()])}")
        
        for service in self.services.keys():
            stderr.print(service)
            if isinstance((service_data := rest_api.get_request(request_info="serviceFullData",safe=False,service=service)),int,):
                stderr.print(f"No services named '{service}' were found. Connection seemed right though!")
                self.services[service]["found_in_system"] = False
                self.services[service]["archived_path"] = None
                self.services[service]["non_archived_path"] = None
            else:
                self.services[service]["found_in_system"] = True
                (self.services[service]["archived_path"], self.services[service]["non_archived_path"],) = get_service_paths(self.conf, self.type, service_data)

            self.services[service]["found"] = []

        # Check on not-found services
        not_found_services = [service for service in self.services.keys() if self.services[service]["found_in_system"] is False]

        if len(not_found_services) != 0:
            # if none of the services was found, exit
            if len(not_found_services) == len(self.services):
                stderr.print(f"NONE of the specified services were found: {','.join(not_found_services)}")
                log.warning(f"NONE of the services chosen has been found: {','.join(not_found_services)}")
                log.info(f"Execution ended automatically due to none of the chosen services being found")
                sys.exit(0)
            else:
                stderr.print(f"The following services were not found on iSkyLIMS: {','.join(not_found_services)}")
                # LOG: some services were not found
                log.warning(f"{len(not_found_services)} services were not found: {','.join(not_found_services)}")
                
                if (bu_isciii.utils.prompt_selection("Continue?", ["Yes, continue", "Exit"])) == "Exit":
                    log.info(f"Execution was ended by the user through prompt after some services were not found: {','.join(not_found_services)}")
                    sys.exit(0)

        # Check on the directories to get location and whether or not it was found
        stderr.print("Finding the services in the directory tree")
        
        for service in self.services.keys():
            if os.path.exists(self.services[service]["archived_path"]):
                self.services[service]["found"].append("Archive")

            if os.path.exists(self.services[service]["non_archived_path"]):
                self.services[service]["found"].append("Data dir")

        if option is None:
            stderr.print("Willing to archive, or retrieve a resolution?")
            self.option = bu_isciii.utils.prompt_selection(
                "Options",
                [
                    "Scout for service size",
                    "Full archive: compress and archive",
                    "    Partial archive: compress NON-archived service",
                    "    Partial archive: archive NON-archived service (must be compressed first) and check md5",
                    "    Partial archive: uncompress newly archived compressed service",
                    "    Partial archive: remove compressed services from directories",
                    "Full retrieve: retrieve and uncompress",
                    "    Partial retrieve: compress archived service",
                    "    Partial retrieve: retrieve archived service (must be compressed first) and check md5",
                    "    Partial retrieve: uncompress retrieved service",
                    "    Partial retrieve: remove compressed services from directories",
                    "Remove selected services from data dir (only if they are already in archive dir)",
                    "That should be all, thank you!",
                ],
            )
        
        # LOG: chosen option
        log.info(f"Chosen option for archive: {self.option.lstrip()}")

    def scout_directory_sizes(self):
        """
        Get size for involved service if the dir has been found,
        Print a table to see said info (service ID, Dir size, where it has been found)
        Generates a log with said info
        """

        log.info("STARTING: Directory scouting")
        log.info("Extracting size of involved directories")

        stderr.print("Extracting the size for the involved directories")
        for service in self.services.keys():
            if "Data dir" in self.services[service]["found"]:
                self.services[service]["non_archived_size"] = get_dir_size(self.services[service]["non_archived_path"]) / pow(1024, 3)
            if "Archive" in self.services[service]["found"]:
                self.services[service]["archived_size"] = get_dir_size(self.services[service]["archived_path"]) / pow(1024, 3)

        # Generate table with the generated info
        size_table = rich.table.Table()
        size_table.add_column("Service ID", justify="center")
        size_table.add_column("Directory size (GB)", justify="center")
        size_table.add_column("Found in", justify="center")

        # Different loop to allow for modifications
        # Reasoning here:
        #   len 0: not found, size "-"
        #   len 2: found in both sides, compare sizes, if different, notify, else, pick archived size (for instance, shouldn't matter)
        #   len 1: if "Archive" in "found", size is archived size, else, non_archived

        for service in self.services.keys():
            if len(self.services[service]["found"]) == 0:
                size = "-"
            elif len(self.services[service]["found"]) == 2:
                if (self.services[service]["archived_size"] != self.services[service]["non_archived_size"]):
                    stderr.print(f"For service {service}, archived size {self.services[service]['archived_size']} and non-archived size {self.services[service]['non_archived_size']} are equal")
                else:
                    size = self.services[service]["non_archived_size"]
            else:
                if "Archive" in self.services[service]["found"]:
                    size = self.services[service]["archived_size"]
                elif "Data dir" in self.services[service]["found"]:
                    size = self.services[service]["non_archived_size"]

            size_table.add_row(
                str(service),
                ("-" if self.services[service]["non_archived_size"] is None else str(self.services[service]["non_archived_size"])),
                (",".join(self.services[service]["found"]) if len(self.services[service]["found"]) > 0 else "Not found in Archive or Data dir"),
            )

        stderr.print(size_table)
        log.info("FINISHED: Directory scouting")

        return

    def targz_directory(self, direction):
        """
        For all chosen services:
        Check no prior .tar.gz file has been created

        Creates the .tar.gz file for all chosen services
        Function created to make a .tar.gz file from a NON-archived directory
        Extracts the MD5 and size as well, to do it all in a single function (might regret later)
        """
        log.info(f"STARTING: Compression of services in the {('Archive' if direction == 'archive' else 'Data')} dir for {direction}.")

        total_initial_size = 0
        total_compressed_size = 0
        newly_compressed_services = []

        # try:
        for service in self.services.keys():

            location_check = "Data dir" if direction == "archive" else "Archive"
            if (location_check not in self.services[service]["found"]):
                log.info(f"Service {service}: not found on the '{location_check}' directory. Skipping")
                continue

            dir_to_tar = (self.services[service]["non_archived_path"] if direction == "archive" else self.services[service]["archived_path"])

            # If dir size has been obtained previously, get it
            # if dir could not be found, pass
            # This could very much be a function on its own
            if direction == "archive":
                if self.services[service]["non_archived_size"] is None:
                    if "Data dir" in self.services[service]["found"]:
                        initial_size = get_dir_size(dir_to_tar) / pow(1024, 3)
                        self.services[service]["non_archived_size"] = initial_size
                    else:
                        stderr.print(f"Service {service} could not be found in the data directory")
                        continue
                else:
                    initial_size = self.services[service]["non_archived_size"]

            else:
                if self.services[service]["archived_size"] is None:
                    if "Archive" in self.services[service]["found"]:
                        initial_size = get_dir_size(dir_to_tar) / pow(1024, 3)
                        self.services[service]["archived_size"] = initial_size
                    else:
                        stderr.print(f"Service {service} could not be found in the archive directory")
                        continue
                else:
                    self.services[service]["archived_size"] = initial_size

            # Check if there is a prior ".tar.gz" file
            # NOTE: I find dir_to_tar + ".tar.gz" easier to mentally locate the compressed files
            if os.path.exists(dir_to_tar + ".tar.gz"):
                
                compressed_size = os.path.getsize(dir_to_tar + ".tar.gz") / pow(1024, 3)
                stderr.print(f"Seems like service {service} has already been compressed in the {location_check} dir\nPath: {dir_to_tar + '.tar.gz'}\nUncompressed size: {initial_size:.3f} GB\nFound compressed size: {compressed_size:.3f} GB")
                
                prompt_response = bu_isciii.utils.prompt_selection("What to do?",["Just skip it",f"Delete previous {service + '.tar.gz'} and compress again",],)
                if (prompt_response.startswith("Delete")) or (self.skip_prompts):
                    if (self.skip_prompts):
                        log.info(f"Service {service}: compressed service {dir_to_tar + '.tar.gz'} was already found. Initial size of the dir: {initial_size:.3f} GB. Compressed size: {compressed_size:.3f} GB. Automatically chosen to DELETE it (no-prompt option activated). Compression process will be performed again.")
                    else:
                        log.info(f"Service {service}: compressed service {dir_to_tar + '.tar.gz'} was already found. Initial size of the dir: {initial_size:.3f} GB. Compressed size: {compressed_size:.3f} GB. User chose to DELETE it through prompt. Compression process will be performed again.")
                        os.remove(dir_to_tar + ".tar.gz")
                else:
                    if direction == "archive":
                        self.services[service]["non_archived_compressed_size"] = compressed_size
                        self.services[service]["compressed"] = "Found already compressed in the data directory"
                        log.info(f"Service {service}: compressed service {dir_to_tar + '.tar.gz'} was already found in the data directory. Initial size of the dir: {initial_size:.3f} GB. Compressed size: {compressed_size:.3f} GB. User chose NOT to delete it through prompt.")                    
                    else:
                        self.services[service]["archived_compressed_size"] = compressed_size
                        self.services[service]["compressed"] = "Found already compressed in the archive directory"
                        log.info(f"Service {service}: compressed service {dir_to_tar + '.tar.gz'} was already found in the archive directory. Initial size of the dir: {initial_size:.3f} GB. Compressed size: {compressed_size:.3f} GB. User chose NOT to delete it through prompt.")   
                    
                    total_initial_size += initial_size
                    total_compressed_size += compressed_size
                    continue

            stderr.print(f"Compressing service {service}")

            try:
                targz_dir(dir_to_tar + ".tar.gz", dir_to_tar)
            except Exception as e:
                stderr.print(f"Compression of service {service} had an error and couldnt be ended. Deleting compressed file and skipping to the next one.")
                
                if os.path.exists(dir_to_tar + ".tar.gz"):
                    os.remove(dir_to_tar + ".tar.gz")
                
                log.info(f"Service {service}: when compressing, a {e} error arised. Ending compression, deleting compressed file and skipping to the next service.")
                self.services[service]["error_status"] = f"Error while compressing the directory: {e}"
                
                
                continue
            compressed_size = os.path.getsize(dir_to_tar + ".tar.gz") / pow(1024, 3)
            
            if direction == "archive":
                self.services[service]["non_archived_compressed_size"] = compressed_size
            else:
                self.services[service]["archived_compressed_size"] = compressed_size

            total_initial_size += initial_size
            total_compressed_size += compressed_size

            stderr.print(f"Service {service} was compressed into {dir_to_tar + '.tar.gz'}")
            stderr.print(f"Initial size: {initial_size:.3f} GB")
            stderr.print(f"Compressed size: {compressed_size:.3f} GB")
            stderr.print(f"Saved space: {initial_size - compressed_size:.3f} GB")
            log.info(f"Service {service}: compression into {dir_to_tar + '.tar.gz'} successful. Initial size: {initial_size:.3f} GB. Compressed size: {compressed_size:.3f} GB. Saved space: {initial_size - compressed_size:.3f} GB.")
            self.services[service]["compressed"] = "Successfuly compressed" 

        # General revision of the compression process
        newly_compressed_services = [service for service in self.services.keys() if self.services[service]["compressed"] == "Successfully compressed"]
        already_compressed_services = [service for service in self.services.keys() if self.services[service]["compressed"] == "Found already compressed"]        

        stderr.print("Compression finished")
        stderr.print(f"Compressed {len(newly_compressed_services + already_compressed_services)} services ({len(newly_compressed_services)} newly compressed, {len(already_compressed_services)} already compressed)")
        stderr.print(f"Total initial size: {total_initial_size:.3f} GB")
        stderr.print(f"Total compressed size: {total_compressed_size:.3f} GB")
        stderr.print(f"Saved space: {total_initial_size - total_compressed_size:.3f} GB")
        stderr.print(f"Newly compressed services: {', '.join(newly_compressed_services)}")
        stderr.print(f"Already compressed services: {', '.join(already_compressed_services)}")

        log.info(f"Compression progress for {direction} finished: {len(newly_compressed_services + already_compressed_services)} services were compressed ({len(newly_compressed_services)} newly compressed, {len(already_compressed_services)} already compressed). Total initial size: {total_initial_size:.3f} GB. Total compressed size: {total_compressed_size:.3f} GB. Saved space: {total_initial_size - total_compressed_size:.3f} GB.")
        log.info(f"Newly compressed services: {', '.join(newly_compressed_services)}")
        log.info(f"Already compressed services: {', '.join(already_compressed_services)}")
        log.info(f"FINISHED: Compression of services in the {('Archive' if direction == 'archive' else 'Data')} dir for {direction}.")
        
        return

    def move_directory(self, direction):
        """
        Move chosen services from a place to another depending on the direction chosen:
            direction = "archive": move service from "non_archived" to "archived"
            direction = "retrieve": move service from "archived" to "non_archived"
        Make sure they are '.tar.gz' files
        """
        log.info(f"STARTING: Compressed service movement ({('Data dir to Archive' if direction == 'archive' else 'Archive to Data dir' )})")

        for service in self.services.keys():          
            (origin, destiny) = ((self.services[service]["non_archived_path"], self.services[service]["archived_path"],) if direction == "archive" else (self.services[service]["archived_path"], self.services[service]["non_archived_path"]))
            
            # If compressed origin cannot be found
            # Check for uncompressed origin
            if not (os.path.exists(origin + ".tar.gz")):
                stderr.print(f"{origin.split('/')[-1] + 'tar.gz'} was not found in the origin directory ({'/'.join(origin.split('/')[:-1])}")
                if os.path.exists(origin):
                    stderr.print(f"Origin path {origin} was found. Please make sure this directory has been compressed.")

                    prompt_response = bu_isciii.utils.prompt_selection("What to do", ["Skip it", "Exit"]
                    if (prompt_response == "Skip it") or (self.skip_prompts):
                        if (self.skip_prompts):
                            stderr.print(f"Skipping service {service} automatically (option skip-prompts activated)")
                            log.info(f"Service {service}: compressed file {origin + '.tar.gz'} was not found. Skipped automatically (option skip-prompts activated).")
                        else:
                            stderr.print(f"Skipping service {service}")
                            log.info(f"Service {service}: compressed file {origin + '.tar.gz'} was not found. Skipped by user through prompt.")
                        continue

                    else:
                        stderr.print("Exiting")
                        log.info(f"Execution ended by user through prompt after service {service} compressed {origin + '.tar.gz'} file was not found in the {direction} process.")
                        sys.exit(0)

                else:
                    stderr.print(f"Origin path {origin} was not found either. Skipping.")
                    log.info(f"Service {service}: neither compressed path ({origin + '.tar.gz'}) or uncompressed path ({origin}) could be found. Skipping.")
                    continue

            # If compresed destiny exists
            if os.path.exists(destiny + ".tar.gz"):
                stderr.print(f"Seems like service ({service}) has already been {direction + 'd'}.")
                prompt_response = bu_isciii.utils.prompt_selection("What to do?",[f"Remove it and {direction} it again", "Ignore this service"],)
                if ("Remove" in prompt_response) or (self.skip_prompts):
                    if (self.skip_prompts):
                        stderr.print(f"Removing {destiny + '.tar.gz'} automatically (option skip-prompts activated).")
                        log.info(f"Service {service}: already found in {destiny + '.tar.gz'}. File removed automatically (option skip-prompts activated), with intention to be copied again.")
                    else:
                        stderr.print(f"Removing {destiny + '.tar.gz'} automatically by user through prompt.")
                        log.info(f"Service {service}: already found in {destiny + '.tar.gz'}. File was removed by user instruction through prompt, with intention to be copied again.")
                    
                    os.remove(destiny + ".tar.gz")
                    stderr.print(f"Removed successfully")
                else:
                    log.info(f"Service {service}: already found in {destiny + '.tar.gz'}. Transference skipped by user through prompt.")
                    continue
            
            origin_md5 = get_md5(origin + ".tar.gz")
            
            # save origin md5
            if direction == "archive":
                self.services[service]["md5_non_archived"] = origin_md5
            else:
                self.services[service]["md5_archived"] = origin_md5
            
            try:
                sysrsync.run(source=origin + ".tar.gz", destination=destiny + ".tar.gz", options=self.conf["options"], sync_source_contents=False,)
                destiny_md5 = get_md5(destiny + ".tar.gz")

                # save destiny md5
                if direction == "archive":
                    self.services[service]["md5_archived"] = destiny_md5
                else:
                    self.services[service]["md5_non_archived"] = destiny_md5

                # compare md5
                if origin_md5 == destiny_md5:
                    stderr.print(f"[green] Service {service}: Data copied successfully from its origin folder ({origin}) to its destiny folder ({destiny}) (MD5: {origin_md5}; identical in both sides)", highlight=False,)
                    log.info(f"Service {service}: copied successfully from {origin}.tar.gz to {destiny}.tar.gz. MD5: {origin_md5}, identical in both sides.)")
                    self.services[service]["moved"] = f"Successfully moved (direction: {direction}), with matching MD5"    
                else:
                    stderr.print(f"[red] ERROR: Service {service}: Data copied from its origin folder ({origin}) to its destiny folder ({destiny}), but MD5 did not match (Origin MD5: {origin_md5}; Destiny MD5: {destiny_md5}).")
                    log.info(f"Service {service}: data copied from its origin folder ({origin}) to its destiny folder ({destiny}), but MD5 did not match (Origin MD5: {origin_md5}; Destiny MD5: {destiny_md5}).")
                    self.services[service]["moved"] = f"Moved (direction: {direction}), MD5 NOT MATCHING."
            except Exception as e:
                stderr.print(f"[red] ERROR: {origin.split('/')[-1] + '.tar.gz'} could not be copied to its destiny archive folder, {destiny}.",highlight=False,)
                log.error(f"Directory {origin} could not be archived to {archived_path}.Reason: {e}")
        
        log.info(f"FINISHED: Compressed service movement ({('Data dir to Archive' if direction == 'archive' else 'Archive to Data dir' )})")
        return

    def uncompress_targz_directory(self, direction):
        """
        Uncompress chosen services
            When archiving, you untar to archived_path
            When retrieving, you untar to non_archived_path
        """

        log.info(f"STARTING: Uncompressing services {('to Data dir for retrieval' if direction == 'retrieve' else 'to Archive dir for archive')}")
        already_uncompressed_services = []
        not_found_compressed_services = []
        successfully_uncompressed_services = []

        for service in self.services.keys():
            dir_to_untar = (self.services[service]["archived_path"] if (direction == "archive") else self.services[service]["non_archived_path"])

            # Check whether the compressed file is not there
            if not os.path.exists(dir_to_untar + ".tar.gz"):
                stderr.print(f"The compressed service { service + '.tar.gz'} could not be found")
                not_found_compressed_services.append(service)

                # Check whether the uncompressed dir is already there
                if os.path.exists(dir_to_untar):
                    stderr.print(f"However, this service is already uncompressed in the destiny folder {'/'.join(dir_to_untar.split('/')[:-1])[:-1]}")
                    self.services[service]["uncompressed"] = f"Could not be uncompressed, compressed file {service + '.tar.gz'} not found on destiny folder {'/'.join(dir_to_untar.split('/')[:-1])[:-1]}. However, the uncompressed service was found."
                    log.info(f"Service {service}: not uncompressed because compressed file was not found. Uncompressed service was found.")
                    continue
                else:
                    stderr.print(f"The uncompressed service, {dir_to_untar} could not be found either.")
                    self.services[service]["uncompressed"] = f"Could not be uncompressed, compressed file not found on destiny folder ({dir_to_untar + '.tar.gz'}). The uncompressed service was not found either."
                    log.info(f"Service {service}: not uncompressed because compressed file was not found. Uncompressed service was NOT found either.")
                    continue
            
            # Compressed file is there
            else:
                if os.path.exists(dir_to_untar):
                    stderr.print(f"Service {service} is already uncompressed in the destiny folder {'/'.join(dir_to_untar.split('/')[:-1])[:-1]}")
                    
                    prompt_response = bu_isciii.utils.prompt_selection("What to do?",["Skip (dont uncompress)",f"Delete uncompressed {service} and uncompress again",],)
                    
                    if (prompt_response.startswith("Delete")) or (self.skip_prompts):
                        if (self.skip_prompts):
                            stderr.print(f"Deleting uncompressed service {service} automatically (option skip-prompts activated)")
                            log.info(f"Service {service}: service was already found uncompressed in the destiny folder {dir_to_untar}. Delete the uncompressed service automatically (option skip-prompt activated) to uncompress it again.")
                        else:
                            stderr.print(f"Deleting uncompressed service {service} by user choice through prompt")
                            log.info(f"Service {service}: service was already found uncompressed in the destiny folder {dir_to_untar}. User decided to delete the uncompressed service through prompt to uncompress it again.")
                        shutil.rmtree(dir_to_untar)
                        stderr.print("Deleted!")
                    else:
                        already_uncompressed_services.append(service)
                        self.services[service]["uncompressed"] = f"Was not uncompressed due to the presence of a previously uncompressed directory"
                        log.info(f"Service {service}: service was already found uncompressed in the destiny folder {dir_to_untar}. User decided to skip uncompression through prompt.")
                        continue
                
                stderr.print(f"Uncompressing {dir_to_untar.split('/')[-1] + '.tar.gz'}")

                uncompress_targz_directory(dir_to_untar + ".tar.gz", dir_to_untar)

                stderr.print(f"Service {service} has been successfully uncompressed")
                log.info(f"Service {service}: successfully uncompressed")
                self.services[service]["uncompressed"] = "Uncompressed successfully"
                successfully_uncompressed_services.append(service)

        stderr.print(f"Uncompressed services: {len(successfully_uncompressed_services)}: {', '.join(successfully_uncompressed_services)}.")
        log.info(f"Uncompressed services: {len(successfully_uncompressed_services)}: {', '.join(successfully_uncompressed_services)}.")

        if len(already_uncompressed_services) > 0:
            stderr.print(f"The following {len(already_uncompressed_services)} service directories were found compressed already: {', '.join(already_uncompressed_services)}")
            log.info(f"Already compressed services: {len(already_uncompressed_services)}: {', '.join(already_uncompressed_services)}")
        
        if len(not_found_compressed_services) > 0:
            stderr.print(f"The following {len(not_found_compressed_services)} services could not be uncompressed because the compressed service could not be found: {', '.join(not_found_compressed_services)}")
            stderr.print(f"Not found compressed services: {len(not_found_compressed_services)}: {', '.join(not_found_compressed_services)}")

        log.info(f"FINISHED: Uncompressing services for {('to Data dir for retrieval' if direction == 'retrieve' else 'to Archive dir for archive')}")
        return

    def delete_targz_dirs(self, direction):
        """
        Delete the targz dirs when the original, uncompressed service is present

        if direction = archive: origin is non-archived, and you are moving to archived
        if direction = retrieve: origin is archive, and you are moving to non-archived     
        
        """
        deleted_services = {
                            "Only origin": [],
                            "Only destiny": [],
                            "Both": [],
                            "None": [],
                            }
        
        file_locations = [[service, self.services[service]["non_archived_path"], self.services[service]["archived_path"]] for service in self.services.keys()] if direction == 'archive' else [[service, self.services[service]["archived_path"], self.services[service]["non_archived_path"]] for service in self.services.keys()]
        origin_folder = "Data directory" if direction == "archive" else "Archive directory"
        destiny_folder = "Archive directory" if direction == "archive" else "Data directory"

        for service, origin, destiny in file_locations:

            if (os.path.exists(origin + ".tar.gz")) and (os.path.exists(destiny + ".tar.gz")):
                
                # Both compressed exist, both uncompressed exist
                if (os.path.exists(origin)) and (os.path.exists(destiny)):
                    stderr.print(f"For service {service}, compressed and uncompressed directories were found in both {origin_folder} and {destiny_folder}. It is safe to delete the compressed files.")
                    
                    os.remove(origin + ".tar.gz")
                    os.remove(destiny + ".tar.gz")
                    
                    log.info(f"Service {service}: both compressed and uncompressed service have been found in the {origin_folder} and the {destiny_folder}. Compressed files deleted.")
                    stderr.print(f"Compressed files for service {service} (in both {origin_folder} and {destiny_folder}) were deleted.")
                    deleted_services["Both"].append(service)

                elif (os.path.exists(origin)) and not (os.path.exists(destiny)):
                    stderr.print(f"For service {service}, compressed directories were found in both the {origin_folder} and the {destiny_folder}. However, the uncompressed directory was NOT found on the {destiny_folder} (therefore, the compressed file will not be deleted).")
                    stderr.print(f"Therefore, it is safe to delete the compressed service in {origin_folder}, but not in the {destiny_folder}")
                    
                    os.remove(origin + ".tar.gz")
                    
                    log.info(f"Service {service}: compressed directory in {origin_folder} was deleted due to presence of the uncompressed directory. Compressed directory in {destiny_folder} was NOT deleted due to absence of the uncompressed directory.")
                    stderr.print(f"Compressed service {service} in {origin_folder} was deleted")


                elif not (os.path.exists(origin)) and (os.path.exists(destiny)):
                    stderr.print(f"For service {service}, compressed directories were found in the {origin_folder} and the {destiny_folder}. However, the uncompressed directory was not found on the {origin_folder}.")
                    stderr.print(f"Therefore, it is NOT safe to delete the compressed service in {origin_folder}, but it is in the {destiny_folder}")
                    
                    os.remove(destiny + ".tar.gz")
                    
                    log.info(f"Service {service}: compressed directory in {origin_folder} was NOT deleted due to absence of the uncompressed directory. Compressed directory in {destiny_folder} was deleted due to presence of the uncompressed directory.")
                    stderr.print(f"Compressed service {service} in {destiny_folder} was deleted")
                else:
                    stderr.print(f"For service {service}, compressed directories were found in the {origin_folder} and the {destiny_folder}. However, the uncompressed directories were not found in the {dorigin_folder} or the {destiny_folder}. Please make sure these services have been uncompressed first.")
                    stderr.print(f"Therefore, it is safe to delete the compressed service in {origin_folder}, but not in the {destiny_folder}")
                    log.info(f"Service {service}: compressed directories in {origin_folder} were NOT deleted due to absence of uncompressed directories in both sides.")
            
            elif (os.path.exists(origin + ".tar.gz")) and not (os.path.exists(destiny + ".tar.gz")):
                if os.path.exists(origin):
                    stderr.print(f"For service {service}, the compressed directory was found in the {origin_folder}, but NOT in the {destiny_folder} (and therefore, it cannot be deleted). Uncompressed directory was found in the {origin_folder}, so it can be deleted.")
                    
                    os.remove(origin + ".tar.gz")

                    log.info(f"Service {service}: compressed directory in {origin_folder} was found and deleted due to presence of the uncompressed directory. Compressed directory in {destiny_folder} could not be deleted because it was not found.")
                    stderr.print(f"Compressed service {service} in {origin_folder} was deleted.")

                else:
                    stderr.print(f"For service {service}, the compressed directory was found in the {origin_folder}, but NOT in the {destiny_folder} (and therefore, it cannot be deleted). Uncompressed directory was NOT found in {origin_folder}, so it should not be deleted either.")
                    log.info(f"Service {service}: compressed directory in {origin_folder} was found, but NOT deleted, due to absence of the uncompressed directory. Compressed directory in {destiny_folder} could not be deleted because it was not found.")
            elif not (os.path.exists(origin + ".tar.gz")) and (os.path.exists(destiny + ".tar.gz")):
                if os.path.exists(destiny):
                    stderr.print(f"For service {service}, the compressed directory was NOT found in the {origin_folder} (and therefore, it cannot be deleted), but it WAS FOUND in the {destiny_folder}. Uncompressed directory was found in the {destiny_folder}, so it can be deleted.")
                    log.info(f"Service {service}: compressed directory in {origin_folder} was NOT found, and could not be deleted. Compressed directory in {destiny_folder} was FOUND and DELETED due to presence of the uncompressed directory.")
               
                else:
                    stderr.print(f"For service {service}, the compressed directory was NOT found in the {origin_folder} (and therefore, it cannot be deleted), but it WAS FOUND in the {destiny_folder}. Uncompressed directory was NOT found in the {destiny_folder}, so it should not be deleted either.")
                    log.info(f"Service {service}: compressed directory in {origin_folder} was NOT found, and could not be deleted. Compressed directory in {destiny_folder} was FOUND, but NOT DELETED due to absence of the uncompressed directory.")
            else: 
                stderr.print(f"For service {service}, NONE of the compressed directories was found (therefore, they cannot be deleted).")
                log.info(f"Service {service}: neither of the compressed directories was found, and therefore they couldnt be deleted.")
                deleted_services["None"].append(service)


        stderr.print(f"Deleted {len(deleted_services)} compressed services: {', '.join(deleted_services)}")
        log.info(f"{len(deleted_services)} compressed services were deleted: {', '.join(deleted_services)}")

        if len(non_deleted_services_not_found) > 0:
            stderr.print(f"{len(non_deleted_services)} compressed services could not be deleted: {', '.join(non_deleted_services)}")
            log.info(f"{len(non_deleted_services)} services were not deleted")
        return

    def delete_non_archived_dirs(self):
        """
        Check that the archived counterpart exists
        Delete the non-archived copy
        NOTE: archived_path should NEVER have to be deleted
        """

        for service in self.services.keys():
            if not os.path.exists(self.services[service]["archived_path"]):
                stderr.print(
                    f"Service {archived_path.split('/')[-1]} has already been removed from {'/'.join(archived_path.split('/')[:-1])[:-1]}. Nothing to delete so skipping.\n"
                )
                # this continue should not be necessary but I think its more efficient
                continue
            else:
                if not os.path.exists(self.services[service]["archived_path"]):
                    stderr.print(
                        f"Archived path for service {self.services[service]['archived_path'].split('/')[-1]} NOT. Skipping.\n"
                    )
                else:
                    stderr.print(
                        f"Found archived path for service {self.services[service]['archived_path'].split('/')[-1]}. It is safe to delete this non_archived service. Deleting.\n"
                    )
                    shutil.rmtree(self.services[service]["non_archived_path"])
        return

    def handle_archive(self):
        """
        Handle archive class options
        """

        if (self.option == "Scout for service size"):
            self.scout_directory_sizes()
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option == "Full archive: compress and archive"):
            self.scout_directory_sizes()
            self.targz_directory(direction="archive")
            self.move_directory(direction="archive")
            self.uncompress_targz_directory(direction="archive")
            self.delete_targz_dirs(direction="archive")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option.lstrip == "Partial archive: compress NON-archived service"):
            self.targz_directory(direction="archive")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option.lstrip() == "Partial archive: archive NON-archived service (must be compressed first) and check md5"):
            self.move_directory(direction="archive")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option.lstrip() == "Partial archive: uncompress newly archived compressed service"):
            self.uncompress_targz_directory(direction="archive")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option.lstrip() == "Partial archive: remove compressed services from directories"):
            self.delete_targz_dirs(direction="archive")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option == "Full retrieve: retrieve and uncompress"):
            self.targz_directory(direction="retrieve")
            self.move_directory(direction="retrieve")
            self.uncompress_targz_directory(direction="retrieve")
            self.delete_targz_dirs(direction="retrieve")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option.lstrip() == "Partial retrieve: compress archived service"):
            self.targz_directory(direction="retrieve")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option.lstrip() == "Partial retrieve: retrieve archived service (must be compressed first) and check md5"):
            self.move_directory(direction="retrieve")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option.lstrip() == "Partial retrieve: uncompress retrieved service"):
            self.uncompress_targz_directory(direction="retrieve")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option.lstrip() == "Partial retrieve: remove compressed services from directories"):
            self.delete_targz_dirs(direction="retrieve")
            generate_tsv_table(self.services, filename="prueba.txt")

        elif (self.option == "Remove selected services from data dir (only if they are already in archive dir)"):
            self.delete_non_archived_dirs()
            generate_tsv_table(self.services, filename="prueba.txt")

        elif self.option == "That should be all, thank you!":
            sys.exit()
        return
