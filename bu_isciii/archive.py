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
    year = bu_isciii.utils.prompt_year(
        lower_limit=lower_limit_year, upper_limit=date.today().year
    )

    # Limit the list to the current month if year = current year
    # This could be a one-liner:
    # month_list = [[num, month] for num, month in enumerate(month_name)][1:] if year < date.today().year else month_list = [[num, month] for num, month in enumerate(month_name)][1:date.today().month+1]
    # I found it easier the following way:
    if year < date.today().year:
        month_list = [[num, month] for num, month in enumerate(calendar.month_name)][1:]
    else:
        month_list = [[num, month] for num, month in enumerate(calendar.month_name)][
            1 : date.today().month + 1
        ]

    # If there is a previous date
    # and year is the same as before, limit the quantity of months
    if previous_date is not None and year == int(previous_date[0]):
        month_list = month_list[int(previous_date[1]) - 1 :]

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

    day_list = list(
        filter(
            None,
            calendar.month(year, int(chosen_month_number))
            .replace("\n", " ")
            .split(" "),
        )
    )[9:]

    # if current month and day, limit the options to the current day
    if year == date.today().year and int(chosen_month_number) == date.today().month:
        day_list = day_list[: date.today().day]

    # if previous date  & same year & same month, limit days
    if (
        previous_date is not None
        and year == int(previous_date[0])
        and chosen_month_number == previous_date[1]
    ):
        day_list = day_list[int(previous_date[2]) - 1 :]

    # from the list, get the first and last item as limits for the function
    day = bu_isciii.utils.prompt_day(
        lower_limit=int(day_list[0]), upper_limit=int(day_list[-1])
    )

    return [str(year), str(chosen_month_number), str(day)]


def get_service_paths(conf, ser_type, service):
    """
    Given a service, a conf and a type,
    get the path it would have in the
    archive, and outside of it

    NOTE: for some services, the 'profileClassificationArea' is None, and the os.path.join may fail
    """
    center = service["serviceUserId"]["profile"]["profileClassificationArea"].lower() if isinstance(service["serviceUserId"]["profile"]["profileClassificationArea"], str) else ""

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
        out_tar.add(directory, arcname="/".join(directory.split("/")[:-1])[:-1])
    return True


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


class Archive:
    """
    Class to perform the storage and retrieval
    of a service
    """

    def __init__(self, resolution_id=None, ser_type=None, year=None, api_token=None,option=None):
        # resolution_id = resolution name (SRVCNM656)
        # ser_type = services_and_colaborations // research
        # option = archive/retrieve

        self.resolution_id = resolution_id
        self.type = ser_type
        self.option = option
        self.services_to_move = []

        # Record of failed services in any of the steps
        self.failed_services = {
            "failed_compression": [],
            "failed_movement" : [],
            "failed_uncompression": [],
        }


        # Get configuration params from configuration.json
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("archive")

        # Get data to connect to the api
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")

        # Initiate API
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )

        if bu_isciii.utils.prompt_selection("Working with a batch, or a single resolution?",["Batch of services", "Single service"],) == "Batch of services":
            stderr.print("Please state the initial date for filtering")
            self.date_from = ask_date()

            stderr.print(
                "Please state the final date for filtering (must be posterior or identical to the initial date)"
            )
            self.date_until = ask_date(previous_date=self.date_from)

            stderr.print(
                f"Asking our trusty API about resolutions between: {'-'.join(self.date_from)} and {'-'.join(self.date_until)}"
            )

            # Ask the API for services within the range
            # safe is False, so instead of exiting, an error code will be returned
            services_batch = rest_api.get_request(
                request_info="services",
                safe=False,
                state="delivered",
                date_from="-".join(self.date_from),
                date_until="-".join(self.date_until),
            )

            # if int (if error code), must be only bc status > 200
            # Check drylab_api.get_request
            if isinstance(services_batch, int):
                stderr.print(
                    f"No services were found in the interval between {'-'.join(self.date_from)} and {'-'.join(self.date_until)}. Connection seemed right though!"
                )
                sys.exit()
            else:
                stderr.print(
                    f"Found {len(services_batch)} service(s) within the interval between {'-'.join(self.date_from)} and {'-'.join(self.date_until)}!"
                )
                if (
                    bu_isciii.utils.prompt_selection(
                        "Continue?", ["Yes, continue", "Hold up"]
                    )
                ) == "Hold up":
                    stderr.print("Exiting")
                    sys.exit()

            # Get individual serviceFullData for each data
            # Not a huge fan of adding the .1 to resolutions honestly
            for service in services_batch:
                request = rest_api.get_request(
                    request_info="serviceFullData",
                    service=f"{service['serviceRequestNumber']}",
                )

                if isinstance(request, int):
                    stderr.print(
                        f"Service '{service['serviceRequestNumber']}' could not be found. Connection seemed right though!"
                    )
                else:
                    self.services_to_move.append(request)

            # services_batch does not seem useful from now on
            # so delete it from memory
            del services_batch

        else:
            self.resolution_id = bu_isciii.utils.prompt_service_id() if self.resolution_id is None else self.resolution_id
            
            stderr.print(
                f"Asking our trusty API about service: {self.resolution_id}"
            )

            # Hold the results in a list so it can be accessed 
            # Just like in batch mode
            self.services_to_move = [
                rest_api.get_request(
                    request_info="serviceFullData",
                    safe=False,
                    service=f"{self.resolution_id}",
                )
            ]

            if isinstance(self.services_to_move[0], int):
                stderr.print(
                    f"No services named '{self.resolution_id}' were found. Connection seemed right though!"
                )
                sys.exit()
        
        # Get configuration params from configuration.json
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("archive")

        # Get data to connect to the api
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration(
            "xtutatis_api_settings"
        )

        # Obtain info from iSkyLIMS api with the conf_api info

        if self.type is None:
            stderr.print("Working with a service, or a research resolution?")
            self.type = bu_isciii.utils.prompt_selection(
                "Type",
                ["services_and_colaborations", "research"],
            )

        if option is None:
            stderr.print("Willing to archive, or retrieve a resolution?")
            self.option = bu_isciii.utils.prompt_selection(
                "Options",
                [
                    "Full archive: compress and archive",
                    "Partial archive: compress NON-archived service", 
                    "Partial archive: archive NON-archived service (must be compressed first) and check md5",       
                    "Partial archive: uncompress newly archived compressed service",
                    "Partial archive: remove newly archived compressed services from DATA directory",
                    "Partial archive: remove newly archived compressed services from ARCHIVED directory",
                    "Full retrieve: retrieve and uncompress",        
                    "Partial retrieve: compress archived service",
                    "Partial retrieve: retrieve archived service (must be compressed first, and check md5",
                    "Partial retrieve: uncompress retrieved service",
                    "That should be all, thank you!",
                ]
            )

    def targz_directory(self, direction):
        """
        For all chosen services:
        Check no prior .tar.gz file has been created

        Creates the .tar.gz file for all chosen services
        Function created to make a .tar.gz file from a NON-archived directory
        Extracts the MD5 and size as well, to do it all in a single function (might regret later)
        """
        total_initial_size = 0
        total_compressed_size = 0
        already_compressed_services = []

        # try:
        for service in self.services_to_move:
            
            # Get path
            _, non_archived_path = get_service_paths(self.conf, self.type, service)
            initial_size = get_dir_size(non_archived_path) / pow(1024, 3)
            # Check if there is a prior "tar.gz" file
            # NOTE: I find non_archived_path + ".tar.gz" easier to locate the compressed files
            if os.path.exists(non_archived_path + ".tar.gz"):
                compressed_size = os.path.getsize(non_archived_path + ".tar.gz") / pow(1024, 3)
                stderr.print(
                    f"Seems like service {non_archived_path.split('/')[-1]} has already been compressed\nPath: {non_archived_path + '.tar.gz'}\nUncompressed size: {initial_size:.3f} GB\nFound compressed size: {compressed_size:.3f} GB")
                
                if (bu_isciii.utils.prompt_selection("What to do?", ["Just skip it", f"Delete previous {non_archived_path.split('/')[-1] + '.tar.gz'}"])) == "Just skip it":
                    total_initial_size += initial_size
                    total_compressed_size += compressed_size
                    already_compressed_services.append(non_archived_path.split('/')[-1])
                    continue
                else:
                    os.remove(non_archived_path + ".tar.gz")

            stderr.print(
                f"Compressing service {non_archived_path.split('/')[-1]}"
            )
            
            targz_dir(non_archived_path + ".tar.gz", non_archived_path)

            compressed_size = os.path.getsize(non_archived_path + ".tar.gz") / pow(
                1024, 3
            )
            
            total_initial_size += initial_size
            total_compressed_size += compressed_size - compressed_size

            stderr.print(
                f"Service {non_archived_path.split('/')[-1]} was compressed\nInitial size: {initial_size:.3f} GB\nCompressed size: {compressed_size:.3f} GB\nSaved space: {initial_size - compressed_size:.3f} GB\n"
            )

        # Just an error placeholder. 
        # TODO: see what errors might arise
        # except IOError:
        #    return False

        stderr.print(
            f"Compressed all {len(self.services_to_move)} services\nTotal initial size: {total_initial_size:.3f} GB\nTotal compressed size: {total_compressed_size:.3f} GB\nSaved space: {total_initial_size - total_compressed_size:.3f} GB"
        )

        if len(already_compressed_services) > 0:
            stderr.print(
                f"Numbers above include the following {len(already_compressed_services)} service directories were found compressed already: {', '.join(already_compressed_services)}"
            )
                
        return

    def move_directory(self, direction):
        """
        Archive selected services
        Make sure they are .tar.gz files
        """

        for service in self.services_to_move:
            # stderr.print(service["servicFolderName"])
            archived_path, non_archived_path = get_service_paths(
                self.conf, self.type, service
            )

            if os.path.exists(non_archived_path):
                stderr.print(
                        f"{archived_path.split('/')[-1]} was not found in the origin directory ({'/'.join(archived_path.split('/'))[:-1]})"
                    )


            if os.path.exists(archived_path) and not os.path.exists(
                archived_path + ".tar.gz"
            ):
                if (
                    self.option
                    == "Partial archive: archive NON-archived directory (must be compressed first)"
                ):
                    stderr.print(
                        f"{archived_path.split('/')[-1] + '.tar.gz'} was not found in the origin directory ({archived_path.split('/')[:-1]}). You have chosen a partial archiving process, make sure this file has been compressed beforehand"
                    )

                    if (
                        bu_isciii.utils.prompt_selection(
                            "Continue?", ["Yes, continue", "Hold up"]
                        )
                    ) == "Hold up":
                        sys.exit()
                    continue

            previous_md5 = get_md5(non_archived_path + ".tar.gz")

            try:
                sysrsync.run(
                    source = non_archived_path + ".tar.gz",
                    destination = archived_path + ".tar.gz",
                    options = self.conf["options"],
                    sync_source_contents = False,
                )

                if previous_md5 == get_md5(archived_path + ".tar.gz"):
                    stderr.print(
                        f"[green] Service {archived_path.split('/')[-1] + 'tar.gz'}: Data copied successfully from its origin folder ({non_archived_path}) to its destiny folder ({archived_path}) (MD5: {previous_md5}; equal in both sides)",
                        highlight=False,
                    )

            except OSError as e:
                stderr.print(
                    f"[red] ERROR: {archived_path.split('/')[-1]} could not be copied to its destiny archive folder.",
                    highlight=False,
                )
                log.error(
                    f"Directory {non_archived_path} could not be archived to {archived_path}.\
                        Reason: {e}"
                )
        return

    def retrieve_from_archive(self):
        """
        Copy a service back from archive
        """
        for service in self.services_to_move:
            # stderr.print(service["servicFolderName"])

            # print(f"archived_path : {self.conf['archived_path']}")
            # print(f"type: {self.type}")
            # print(
            #     f"profileCenter: {service['serviceUserId']['profile']['profileCenter']}"
            #)
            # print(
            #    f"Area: {service['serviceUserId']['profile']['profileClassificationArea'].lower()}"
            #)

            archived_path, non_archived_path = get_service_paths(
                self.conf, self.type, service
            )

            try:
                sysrsync.run(
                    source=archived_path + ".tar.gz",
                    destination=non_archived_path + ".tar.gz",
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

    def handle_archive(self):
        """
        Handle archive class options
        """
        if (self.option == "Full archive: compress and archive"):
            self.targz_directory(direction="archive")
            self.move_directory(direction="archive")
            self.uncompress_targz_directory(direction="archive")
        
        elif (self.option == "Partial archive: compress NON-archived service"):
            self.targz_directory(direction="archive")

        elif (self.option == "Partial archive: archive NON-archived service (must be compressed first) and check md5"):
            self.move_directory(direction="archive")
        
        elif (self.option == "Partial archive: uncompress newly archived compressed service"):
            # self.uncompress_targz_directory(direction="archive")
            stderr.print("This is not ready yet, Im on it!")

        elif (self.option == "Partial archive: remove newly archived compressed services from DATA directory"):
            stderr.print("This is not ready yet, Im on it!")

        elif (self.option == "Partial archive: remove newly archived compressed services from ARCHIVED directory"):
            stderr.print("This is not ready yet, Im on it!")

        elif (self.option == "Full retrieve: retrieve and uncompress"):
            # self.targz_directory(direction="retrieve")
            # self.move_directory(direction="retrieve")
            # self.uncompress_targz_directory(direction="retrieve")

        elif (self.option == "Partial retrieve: compress archived service"):
            # self.targz_directory(direction="retrieve")
            stderr.print("This is not ready yet, Im on it!")

        elif (self.option == "Partial retrieve: retrieve archived service (must be compressed first) and check md5"):
            # self.move_directory(direction="retrieve")
            stderr.print("This is not ready yet, Im on it!")

        elif (self.option == "Partial retrieve: uncompress retrieved service"):
            # self.uncompress_targz_directory(direction="retrieve")
            stderr.print("This is not ready yet, Im on it!")

        elif (self.option == "That should be all, thank you!"):
            sys.exit()
        return
