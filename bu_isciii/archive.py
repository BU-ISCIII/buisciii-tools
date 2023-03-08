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


def ask_date(previous_date=None, initial_year=2010):
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
    year = bu_isciii.utils.prompt_year(
        lower_limit=lower_limit_year, upper_limit=datetime.date.today().year
    )

    # Limit the list to the current month if year = current year
    # This could be a one-liner:
    # month_list = [[num, month] for num, month in enumerate(month_name)][1:] if year < date.today().year else month_list = [[num, month] for num, month in enumerate(month_name)][1:date.today().month+1]
    # I found it easier the following way:
    if year < datetime.date.today().year:
        month_list = [[num, month] for num, month in enumerate(calendar.month_name)][1:]
    else:
        month_list = [[num, month] for num, month in enumerate(calendar.month_name)][
            1 : datetime.date.today().month + 1
        ]

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

    day_list = list(
        filter(
            None,
            calendar.month(year, int(chosen_month_number))
            .replace("\n", " ")
            .split(" "),
        )
    )[9:]

    # if current month and day, limit the options to the current day
    if (
        year == datetime.date.today().year
        and int(chosen_month_number) == datetime.date.today().month
    ):
        day_list = day_list[: datetime.date.today().day]

    # if previous date  & same year & same month, limit days
    if (
        previous_date is not None
        and year == previous_date.year
        and chosen_month_number == previous_date.month
    ):
        day_list = day_list[previous_date.day - 1 :]

    # from the list, get the first and last item as limits for the function
    day = bu_isciii.utils.prompt_day(
        lower_limit=int(day_list[0]), upper_limit=int(day_list[-1])
    )

    return datetime.date([year, chosen_month_number, day])


def validate_date(date, previous_date=None):
    pass

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


class Archive:
    """
    Class to perform the storage and retrieval
    of a service
    """

    def __init__(self, service_id=None, ser_type=None, option=None, api_token=None):
        # resolution_id = resolution name (SRVCNM656)
        # ser_type = services_and_colaborations // research
        # option = archive/retrieve

        self.type = ser_type
        self.option = option
        self.services = {
            resolution_id: {
                "found_in_system": "",
                "archived_path": "",
                "non_archived_path": "",
                "found": [],
                "archived_size": int(),
                "non_archived_size": int(),
            }
        }

        # Record of failed services in any of the steps
        # self.service_info = {
        #     "failed_compression": [],
        #     "failed_movement": [],
        #     "failed_uncompression": [],}

        # Get configuration params from configuration.json
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("archive")
        # Get data to connect to the api
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("xtutatis_api_settings")
        
        # Initiate API
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )

        if self.type is None:
            stderr.print("Working with a service, or a research resolution?")
            self.type = bu_isciii.utils.prompt_selection(
                "Type",
                ["services_and_colaborations", "research"],
            )

        if (
            bu_isciii.utils.prompt_selection(
                "Search services by date, or by resolution ID?",
                ["Search by date", "Resolution ID"],
            )
            == "Search by date"
        ):
            stderr.print("Please state the initial date for filtering")
            self.date_from = ask_date()

            stderr.print(
                "Please state the final date for filtering (must be posterior or identical to the initial date)"
            )
            self.date_until = ask_date(previous_date=self.date_from)

            stderr.print(
                f"Asking our trusty API about resolutions between: {self.date_from} and {self.date_until}"
            )

            self.services = {
                service["serviceRequestNumber"]: {"found_in_system": True}
                for service in rest_api.get_request(
                    request_info="services",
                    safe=False,
                    state="delivered",
                    date_from=str(self.date_from),
                    date_until=str(self.date_until),
                )
            }

        else:
            if len(self.services.keys()) == 1 and self.services.keys([0]) is None:
                self.services[bu_isciii.utils.prompt_service_id()] = {}

            # Ask if more services will be chosen
            while True:
                if (
                    bu_isciii.utils.prompt_selection(
                        "Would you like to add any other service?",
                        ["Add more services", "Do not add more services"],
                    )
                    == "Do not add more services"
                ):
                    break
                else:
                    self.services[bu_isciii.utils.prompt_service_id()]

        for service in self.services.keys():
            stderr.print(f"Asking our trusty API about service: {service}")

            if isinstance(
                (
                    service_data := rest_api.get_request(
                        request_info="serviceFullData",
                        safe=False,
                        service=service
                    )
                ),
                int,
            ):
                stderr.print(
                    f"No services named '{service}' were found. Connection seemed right though!"
                )
                self.services[service]["found_in_system"] = False
                self.services[service]["archived_path"] = None
                self.services[service]["non_archived_path"] = None
            else:
                self.services[service]["found_in_system"] = True
                (
                    self.services[service]["archived_path"],
                    self.services[service]["non_archived_path"],
                ) = get_service_paths(self.conf, self.type, service_data)

        # Check on not-found services
        not_found_services = [service for service in self.services.keys() if self.services[service]["found_in_system"] is False]
        if len(not_found_services) == len(self.services):
            stderr.print(f"None of the specified services was found: {','.join(not_found_services)[:-1]}")
            sys.exit(0)
        elif len(not_found_services) == 0:
            pass
        else:
            stderr.print(f"The following services were not found on iSkyLIMS: {','.join(not_found_services)[:-1]}")
            if (bu_isciii.utils.prompt_selection("Continue?", ["Yes, continue", "Hold up"])) == "Hold up":
                        sys.exit()

        # Check on the directories to get location and size
        stderr.print("Finding the services in the directory tree")
        for service in self.services.keys():

            if os.path.exists(self.services[service]["archived_path"]):
                self.services[service]["found"].append("Archive")
                self.services[service]["archived_size"] = get_dir_size(self.services[service]["archived_path"]) / pow(1024, 3)
            else:
                self.services[service]["archived_size"] = 0

            if os.path.exists(self.services[service]["non_archived_path"]):
                self.services[service]["found"].append("Data dir")
                self.services[service]["non_archived_size"] = get_dir_size(self.services[service]["non_archived_path"]) / pow(1024, 3)
            else:
                self.services[service]["non_archived_size"] = 0

        # Generate the table
        size_table = rich.table.Table()
        
        size_table.add_column("Service ID")
        size_table.add_column("Directory size")
        size_table.add_column("Found in")

        for service in self.services.keys():
            table.add_row(
                service,
                services[service]["non_archived_path"],
                services[service]["found"]
            )
    
        if option is None:
            stderr.print("Willing to archive, or retrieve a resolution?")
            self.option = bu_isciii.utils.prompt_selection(
                "Options",
                [
                    "Scout for service size"
                    "Full archive: compress and archive",
                    "    Partial archive: compress NON-archived service",
                    "    Partial archive: archive NON-archived service (must be compressed first) and check md5",
                    "    Partial archive: uncompress newly archived compressed service",
                    "    Partial archive: remove compressed services from directories",
                    "Full retrieve: retrieve and uncompress",
                    "    Partial retrieve: compress archived service",
                    "    Partial retrieve: retrieve archived service (must be compressed first) and check md5",
                    "    Partial retrieve: uncompress retrieved service",
                    "Remove selected services from data dir (only if they are already in archive dir)",
                    "That should be all, thank you!",
                ],
            )

    def scout_directory_sizes(self):

        pass

        return


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
            # Get paths (archived and non-archived counterparts)
            archived_path, non_archived_path = get_service_paths(
                self.conf, self.type, service
            )

            # Identify
            dir_to_tar = non_archived_path if direction == "archive" else archived_path

            initial_size = get_dir_size(dir_to_tar) / pow(1024, 3)

            # Check if there is a prior ".tar.gz" file
            # NOTE: I find dir_to_tar + ".tar.gz" easier to mentally locate the compressed files
            if os.path.exists(dir_to_tar + ".tar.gz"):
                compressed_size = os.path.getsize(dir_to_tar + ".tar.gz") / pow(1024, 3)
                stderr.print(
                    f"Seems like service {dir_to_tar.split('/')[-1]} has already been compressed\nPath: {dir_to_tar + '.tar.gz'}\nUncompressed size: {initial_size:.3f} GB\nFound compressed size: {compressed_size:.3f} GB"
                )

                if (
                    bu_isciii.utils.prompt_selection(
                        "What to do?",
                        [
                            "Just skip it",
                            f"Delete previous {dir_to_tar.split('/')[-1] + '.tar.gz'} and compress again",
                        ],
                    )
                ) == "Just skip it":
                    total_initial_size += initial_size
                    total_compressed_size += compressed_size
                    already_compressed_services.append(dir_to_tar.split("/")[-1])
                    continue
                else:
                    os.remove(dir_to_tar + ".tar.gz")

            stderr.print(f"Compressing service {dir_to_tar.split('/')[-1]}")

            targz_dir(dir_to_tar + ".tar.gz", dir_to_tar)

            compressed_size = os.path.getsize(dir_to_tar + ".tar.gz") / pow(1024, 3)

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
            f"\nCompressed all {len(self.services_to_move)} services\nTotal initial size: {total_initial_size:.3f} GB\nTotal compressed size: {total_compressed_size:.3f} GB\nSaved space: {total_initial_size - total_compressed_size:.3f} GB\n"
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

            [origin, destiny] = (
                [non_archived_path, archived_path]
                if direction == "archive"
                else [archived_path, non_archived_path]
            )

            # If origin cant be found, next
            if not (os.path.exists(origin + ".tar.gz")):
                stderr.print(
                    f"{origin.split('/')[-1] + 'tar.gz'} was not found in the origin directory ({'/'.join(origin.split('/')[:-1])})"
                )
                continue

            # If origin is found, but no compressed origin
            if (os.path.exists(origin)) and not (os.path.exists(origin + ".tar.gz")):
                if (
                    self.option
                    == "    Partial archive: archive NON-archived service (must be compressed first) and check md5"
                ) or (
                    self.option
                    == "    Partial retrieve: retrieve archived service (must be compressed first) and check md5"
                ):
                    stderr.print(
                        f"{archived_path.split('/')[-1] + '.tar.gz'} was not found in the origin directory ({archived_path.split('/')[:-1]}). You have chosen a partial process, make sure this file has been compressed beforehand"
                    )
                    if (
                        bu_isciii.utils.prompt_selection(
                            "Continue?", ["Yes, continue", "Hold up"]
                        )
                    ) == "Hold up":
                        sys.exit()
                # else:
                # si es un total archive o total retrieve,
                # revisar en el diccionario de fails si ha fallado en el paso de compresión
                continue

            # If compresed destiny exists
            if os.path.exists(destiny + ".tar.gz"):
                stderr.print(
                    f"Seems like this service ({destiny.split('/')[-1]}) has already been {direction + 'd'}"
                )
                # SHOW SIZE OF ORIGINAL AND SIZE OF COMPRESSED FILE?
                if (
                    bu_isciii.utils.prompt_selection(
                        "What to do?",
                        [f"Remove it and {direction} it again", "Ignore this service"],
                    )
                ) == "Ignore this service":
                    continue
                else:
                    os.remove(destiny + ".tar.gz")

            origin_md5 = get_md5(origin + ".tar.gz")

            try:
                sysrsync.run(
                    source=origin + ".tar.gz",
                    destination=destiny + ".tar.gz",
                    options=self.conf["options"],
                    sync_source_contents=False,
                )

                if origin_md5 == get_md5(destiny + ".tar.gz"):
                    stderr.print(
                        f"[green] Service {origin.split('/')[-1] + 'tar.gz'}: Data copied successfully from its origin folder ({origin}) to its destiny folder ({destiny}) (MD5: {origin_md5}; identical in both sides)",
                        highlight=False,
                    )

            except OSError as e:
                stderr.print(
                    f"[red] ERROR: {origin.split('/')[-1] + '.tar.gz'} could not be copied to its destiny archive folder, {destiny}.",
                    highlight=False,
                )
                log.error(
                    f"Directory {origin} could not be archived to {archived_path}.\
                        Reason: {e}"
                )
        return

    def uncompress_targz_directory(self, direction):
        """
        Uncompress chosen services
        """

        already_uncompressed_services = []

        for service in self.services_to_move:
            archived_path, non_archived_path = get_service_paths(
                self.conf, self.type, service
            )

            # When archiving, you untar to archived_path
            # When retrieving, you untar to non_archived_path
            dir_to_untar = (
                archived_path if (direction == "archive") else non_archived_path
            )

            # Check whether the compressed file is not there
            if not os.path.exists(dir_to_untar + ".tar.gz"):
                stderr.print(
                    f"The compressed service { dir_to_untar.split('/')[-1] + '.tar.gz'} could not be found"
                )

                # Check whether the uncompressed dir is already there
                if os.path.exists(dir_to_untar):
                    stderr.print(
                        f"However, like this service is already uncompressed in the destiny folder {'/'.join(dir_to_untar.split('/')[:-1])[:-1]}"
                    )
                else:
                    stderr.print(
                        f"The uncompressed service, {dir_to_untar} could not be found either."
                    )
                    continue
            else:
                if os.path.exists(dir_to_untar):
                    stderr.print(
                        f"This service is already uncompressed in the destiny folder {'/'.join(dir_to_untar.split('/')[:-1])[:-1]}"
                    )
                    if (
                        bu_isciii.utils.prompt_selection(
                            "What to do?",
                            [
                                "Skip (dont uncompress)",
                                f"Delete {dir_to_untar.split('/')[-1]} and uncompress again",
                            ],
                        )
                        == "Skip (dont uncompress)"
                    ):
                        already_uncompressed_services.append(
                            dir_to_untar.split("/")[-1]
                        )
                        continue
                    else:
                        shutil.rmtree(dir_to_untar)

                stderr.print(f"Uncompressing {dir_to_untar.split('/')[-1] + '.tar.gz'}")
                uncompress_targz_directory(dir_to_untar + ".tar.gz", dir_to_untar)
                stderr.print(
                    f"{dir_to_untar.split('/')[-1]} has been successfully uncompressed"
                )

        stderr.print(f"\nUncompressed all {len(self.services_to_move)} services")

        if len(already_uncompressed_services) > 0:
            stderr.print(
                f"The following {len(already_uncompressed_services)} service directories were found compressed already: {', '.join(already_uncompressed_services)}"
            )

        return

    def delete_targz_dirs(self, direction):
        """
        Delete the targz dirs when the original, uncompressed service is present
        The origin directory will always be deleted last
        This is:
            Direction "archive": archived compressed dir will be deleted first bc the original dir is in non_archived
            Direction "retrieve": non_archived compressed dir will be deleted first bc the original dir is in archive
        """

        non_deleted_services = []

        for service in self.services_to_move:
            archived_path, non_archived_path = get_service_paths(
                self.conf, self.type, service
            )

            # Origin will always be deleted last
            # [destiny, origin]
            file_locations = (
                [non_archived_path, archived_path]
                if direction == "archive"
                else [archived_path, non_archived_path]
            )

            # First we delete origin
            # Check if there is a non-compressed
            for place in file_locations:
                if os.path.exists(place):
                    stderr.print(
                        f"Uncompressed service {place.split('/')[-1]} has been found in the destiny folder {'/'.join(place.split('/')[:-1])}, so there should be no problem deleting the compressed file {place.split('/')[-1] + '.tar.gz'}. Deleting.\n"
                    )
                    os.remove(place + ".tar.gz")

                else:
                    stderr.print(
                        f"Uncompressed service {place.split('/')[-1]} NOT FOUND in the folder {'/'.join(place.split('/')[:-1])}"
                    )

                    if (
                        bu_isciii.utils.prompt_selection(
                            "What to do?", ["Skip deletion", "Delete anyways"]
                        )
                        == "Skip deletion"
                    ):
                        non_deleted_services.append(place.split("/")[-1])
                        continue
                    else:
                        os.remove(place + ".tar.gz")

        stderr.print(
            f"Deleted {2*len(self.services_to_move) - len(non_deleted_services)} compressed services."
        )
        if len(non_deleted_services) > 0:
            stderr.print(
                f"{len(non_deleted_services)} compressed services could not be deleted: {', '.join(non_deleted_services)}"
            )

        return

    def delete_non_archived_dirs(self):
        """
        Check that the archived counterpart exists
        Delete the non-archived copy
        NOTE: archived_path should NEVER have to be deleted
        """
        for service in self.services_to_move:
            archived_path, non_archived_path = get_service_paths(
                self.conf, self.type, service
            )

            if not os.path.exists(non_archived_path):
                stderr.print(
                    f"Service {archived_path.split('/')[-1]} has already been removed from {'/'.join(archived_path.split('/')[:-1])[:-1]}. Nothing to delete so skipping.\n"
                )
                # this continue should not be necessary but I think its more efficient
                continue
            else:
                if not os.path.exists(archived_path):
                    stderr.print(
                        f"Archived path for service {archived_path.split('/')[-1]} NOT. Skipping.\n"
                    )
                else:
                    stderr.print(
                        f"Found archived path for service {archived_path.split('/')[-1]}. It is safe to delete this non_archived service. Deleting.\n"
                    )
                    shutil.rmtree(non_archived_path)
        return

    def handle_archive(self):
        """
        Handle archive class options
        """

        if self.option == "Scout for service size":
            pass
        elif self.option == "Full archive: compress and archive":
            self.targz_directory(direction="archive")
            self.move_directory(direction="archive")
            self.uncompress_targz_directory(direction="archive")
            self.delete_targz_dirs(direction="archive")
            self.delete_non_archived_dirs()

        elif self.option == "    Partial archive: compress NON-archived service":
            self.targz_directory(direction="archive")

        elif (
            self.option
            == "    Partial archive: archive NON-archived service (must be compressed first) and check md5"
        ):
            self.move_directory(direction="archive")

        elif (
            self.option
            == "    Partial archive: uncompress newly archived compressed service"
        ):
            self.uncompress_targz_directory(direction="archive")

        elif (
            self.option
            == "    Partial archive: remove compressed services from directories"
        ):
            self.delete_targz_dirs(direction="archive")

        elif self.option == "Full retrieve: retrieve and uncompress":
            self.targz_directory(direction="retrieve")
            self.move_directory(direction="retrieve")
            self.uncompress_targz_directory(direction="retrieve")
            self.delete_targz_dirs(direction="retrieve")

        elif self.option == "    Partial retrieve: compress archived service":
            self.targz_directory(direction="retrieve")

        elif (
            self.option
            == "    Partial retrieve: retrieve archived service (must be compressed first) and check md5"
        ):
            self.move_directory(direction="retrieve")

        elif self.option == "    Partial retrieve: uncompress retrieved service":
            self.uncompress_targz_directory(direction="retrieve")

        elif (
            self.option
            == "    Partial retrieve: remove compressed services from directories"
        ):
            self.delete_targz_dirs(direction="retrieve")

        elif (
            self.option
            == "Remove selected services from data dir (only if they are already in archive dir)"
        ):
            self.delete_non_archived_dirs()

        elif self.option == "That should be all, thank you!":
            sys.exit()
        return
