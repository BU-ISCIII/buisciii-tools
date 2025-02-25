#!/usr/bin/env python

import logging
import os
import shutil
import sys
from math import pow

import rich
import sysrsync

import buisciii
import buisciii.config_json
import buisciii.drylab_api
import buisciii.utils

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


class Archive:
    """
    This class handles archive of active services and retrieval of archived services, from/to the
    respectives folders / repositories
    """

    def __init__(
        self,
        service_id=None,
        services_file=None,
        ser_type=None,
        option=None,
        api_user=None,
        api_password=None,
        conf=None,
        skip_prompts=False,
        date_from=None,
        date_until=None,
        output_name=None,
    ):
        log.info("Activated archive module of the bu-isciii tools")

        if output_name:
            self.output_name = output_name
        else:
            self.output_name = buisciii.utils.prompt_path(
                "Write output path with filename for tsv output:"
            )

        self.services = {}
        dictionary_template = {
            "found_in_system": "",
            "delivery_date": "",
            "archived_path": "",
            "non_archived_path": "",
            "archived_size": int(),
            "archived_compressed_size": int(),
            "non_archived_size": int(),
            "non_archived_compressed_size": int(),
            "found": [],
            "same_size": bool,
            "md5_non_archived": "",
            "md5_archived": "",
            "compressed": "No compression performed",
            "copied": "No movement performed",
            "uncompressed": "No uncompression performed",
            "deleted": "No deletion performed",
            "error_status": "No errors detected",
        }

        # Get configuration params from configuration.json
        # Get data to connect to the API
        self.conf = conf.get_configuration("archive")
        conf_api = conf.get_configuration("api_settings")

        # Initiate API
        rest_api = buisciii.drylab_api.RestServiceApi(
            conf_api["server"],
            conf_api["api_url"],
            api_user,
            api_password,
        )

        self.skip_prompts = skip_prompts
        self.option = option
        self.date_from = date_from
        self.date_until = date_until

        if ser_type is None or ser_type not in [
            "services_and_colaborations",
            "research",
        ]:
            stderr.print("Working with a service, or a research resolution?")
            self.ser_type = buisciii.utils.prompt_selection(
                "Type",
                ["services_and_colaborations", "research"],
            )
        else:
            self.ser_type = ser_type

        log.info(f"Service type chosen: {self.ser_type}")

        if ((date_from is None) and (date_until is not None)) or (
            (date_from is not None) and (date_until is None)
        ):
            stderr.print(
                f"Initial date was {('not' if date_from is None else '')} set, "
                f"but Final date was {('not' if date_until is None else '')}. Please provide both!"
            )
            sys.exit()

        if (
            (
                (date_from is not None)
                and (date_until is not None)
                and (service_id is not None)
            )
            or (
                (date_from is not None)
                and (date_until is not None)
                and (services_file is not None)
            )
            or ((services_file) is not None and (service_id) is not None)
        ):
            stderr.print(
                "Both a date and a service ID or service list have been chosen. "
            )
            prompt_response = buisciii.utils.prompt_selection(
                "Which one would you like to keep?",
                ["Search by date", "Search by ID", "Search using file"],
            )
            if (prompt_response) == "Search by date":
                service_id = None
                services_file = None
            elif (prompt_response) == "Search by ID":
                date_from = None
                date_until = None
                services_file = None
            elif (prompt_response) == "Search using file":
                date_from = None
                date_until = None
                service_id = None

        if (
            (date_from is None)
            and (date_until is None)
            and (service_id is None)
            and (services_file is None)
        ):
            if self.ser_type == "services_and_colaborations":
                prompt_response = buisciii.utils.prompt_selection(
                    "Search services by date, or by service ID?",
                    ["Search by date", "Service ID"],
                )
            else:
                prompt_response = "Service ID"

            log.info("Services chosen by: " + prompt_response)
            if prompt_response == "Search by date":
                stderr.print("Please state the initial date for filtering")
                self.date_from = buisciii.utils.ask_date()
                stderr.print(
                    "Please state the final date for filtering (must be posterior or identical to the initial date)"
                )
                self.date_until = buisciii.utils.ask_date(previous_date=self.date_from)

                log.info(f"Starting date: {self.date_from} (chosen through prompt)")
                log.info(f"Ending date: {self.date_until} (chosen through prompt)")
                stderr.print(
                    f"Asking our trusty API about resolutions between: {self.date_from} and {self.date_until}"
                )
            elif prompt_response == "Service ID":
                service_id = buisciii.utils.prompt_service_id()
                self.services = {
                    service_id: {
                        key: value for key, value in dictionary_template.items()
                    }
                }
                log.info(f"Chosen service: {service_id} (chosen through prompt)")

                # Ask if more services will be chosen
                while True:
                    prompt_response = buisciii.utils.prompt_selection(
                        "Would you like to add any other service?",
                        ["Add more services", "Do not add more services"],
                    )
                    if prompt_response == "Do not add more services":
                        break
                    else:
                        new_service = buisciii.utils.prompt_service_id()
                        self.services[new_service] = {
                            key: value for key, value in dictionary_template.items()
                        }
                        log.info(
                            f"Chosen service: {new_service} (chosen through prompt)"
                        )
        else:
            self.date_from = date_from
            self.date_until = date_until
            if service_id:
                self.services = (
                    {
                        service_id: {
                            key: value for key, value in dictionary_template.items()
                        }
                    }
                    if service_id is not None
                    else dict()
                )
            elif services_file:
                with open(services_file) as file:
                    for s_id in file:
                        self.services[s_id] = {
                            key: value for key, value in dictionary_template.items()
                        }

        if (self.date_from is not None) and (self.date_until is not None):
            stderr.print("Asking our trusty API about selected services")
            try:
                for service in rest_api.get_request(
                    request_info="services",
                    safe=True,
                    state="delivered",
                    date_from=str(self.date_from),
                    date_until=str(self.date_until),
                ):
                    self.services[service["service_request_number"]] = {
                        key: value for key, value in dictionary_template.items()
                    }
                    self.services[service["service_request_number"]][
                        "found_in_system"
                    ] = True
                    self.services[service["service_request_number"]][
                        "delivery_date"
                    ] = service["service_delivered_date"]

                log.info(f"Services found in the time interval: {len(self.services)}")
                log.info(
                    "Names of the services found in said interval:"
                    f"{','.join([service for service in self.services.keys()])}"
                )
            except TypeError:
                stderr.print(
                    "Could not connect to the API (wrong password?)", style="red"
                )
                log.error(
                    "Connection to the API was not successful. Possible reasons: wrong API password, bad connection."
                )
                sys.exit(1)

        for service in self.services.keys():
            stderr.print(service)
            if self.ser_type == "services_and_colaborations":
                if isinstance(
                    (
                        service_data := rest_api.get_request(
                            request_info="service-data", safe=True, service=service
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
                    self.services[service]["archived_path"] = os.path.join(
                        buisciii.utils.get_service_paths(
                            conf, self.ser_type, service_data, "archived_path"
                        ),
                        service_data["resolutions"][0]["resolution_full_number"],
                    )

                    self.services[service]["non_archived_path"] = os.path.join(
                        buisciii.utils.get_service_paths(
                            conf, self.ser_type, service_data, "non_archived_path"
                        ),
                        service_data["resolutions"][0]["resolution_full_number"],
                    )
            else:
                self.services[service]["found_in_system"] = True
                self.services[service]["archived_path"] = os.path.join(
                    conf.get_configuration("global")["archived_path"],
                    self.ser_type,
                    service_id,
                )
                self.services[service]["non_archived_path"] = os.path.join(
                    conf.get_configuration("global")["data_path"],
                    self.ser_type,
                    service_id,
                )

            self.services[service]["found"] = []

        # Check on not-found services
        not_found_services = [
            service
            for service in self.services.keys()
            if self.services[service]["found_in_system"] is False
        ]

        if not_found_services:
            # if none of the services was found, exit
            if len(not_found_services) == len(self.services):
                stderr.print(
                    f"NONE of the specified services were found: {','.join(not_found_services)}"
                )
                log.warning(
                    f"NONE of the services chosen has been found: {','.join(not_found_services)}"
                )
                log.info(
                    "Execution ended automatically due to none of the chosen services being found"
                )
                sys.exit(0)
            else:
                stderr.print(
                    f"The following services were not found on iSkyLIMS: {','.join(not_found_services)}"
                )
                # LOG: some services were not found
                log.warning(
                    f"{len(not_found_services)} services were not found: {','.join(not_found_services)}"
                )
                if not self.skip_prompts:
                    if (
                        buisciii.utils.prompt_selection(
                            "Continue?", ["Yes, continue", "Exit"]
                        )
                    ) == "Exit":
                        log.info(
                            "Execution was ended by the user through prompt after some services were not found:"
                            f"{','.join(not_found_services)}"
                        )
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
            self.option = buisciii.utils.prompt_selection(
                "Options",
                [
                    "Scout for service size",
                    "Full archive: compress and archive",
                    "    Partial archive: compress NON-archived service",
                    "    Partial archive: archive NON-archived service (must be compressed first) and check md5",
                    "    Partial archive: uncompress newly archived compressed service",
                    "Full retrieve: retrieve and uncompress",
                    "    Partial retrieve: compress archived service",
                    "    Partial retrieve: retrieve archived service (must be compressed first) and check md5",
                    "    Partial retrieve: uncompress retrieved service",
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

        # Generate table with the generated info
        size_table = rich.table.Table()
        size_table.add_column("Service ID", justify="center")
        size_table.add_column("Directory size (GB)", justify="center")
        size_table.add_column("Found in", justify="center")

        for service in self.services.keys():
            if "Data dir" in self.services[service]["found"]:
                self.services[service]["non_archived_size"] = (
                    buisciii.utils.get_dir_size(
                        self.services[service]["non_archived_path"]
                    )
                    / pow(1024, 3)
                )
            if "Archive" in self.services[service]["found"]:
                self.services[service]["archived_size"] = buisciii.utils.get_dir_size(
                    self.services[service]["archived_path"]
                ) / pow(1024, 3)

            if (
                self.services[service]["archived_size"]
                == self.services[service]["non_archived_size"]
            ):
                self.services[service]["same_size"] = True
            else:
                self.services[service]["same_size"] = False

            if size_table.row_count < 10:
                size_table.add_row(
                    str(service),
                    (
                        "-"
                        if self.services[service]["non_archived_size"] is None
                        else str(self.services[service]["non_archived_size"])
                    ),
                    (
                        ",".join(self.services[service]["found"])
                        if len(self.services[service]["found"]) > 0
                        else "Not found in Archive or Data dir"
                    ),
                )

        stderr.print(
            "Only the first 10 lines of the table will be shown here. Please check the csv for the complete info."
        )
        stderr.print(size_table)
        log.info("FINISHED: Directory scouting")
        return

    def targz_directory(self, direction):
        """
        For all chosen services:
        Check no prior .tar.gz file has been created
        Creates the .tar.gz file for all chosen services
        """
        log.info(
            f"STARTING: Compression of services in the {('Archive' if direction == 'archive' else 'Data')} dir "
            f"for {direction}."
        )

        total_initial_size = 0
        total_compressed_size = 0
        newly_compressed_services = []

        # try:
        for service in self.services.keys():
            location_check = "Data dir" if direction == "archive" else "Archive"
            if location_check not in self.services[service]["found"]:
                log.info(
                    f"Service {service}: not found on the '{location_check}' directory. Skipping"
                )
                continue

            dir_to_tar = (
                self.services[service]["non_archived_path"]
                if direction == "archive"
                else self.services[service]["archived_path"]
            )

            # If dir size has been obtained previously, get it
            # if dir could not be found, pass
            # This could very much be a function on its own
            if direction == "archive":
                initial_size = self.services[service]["non_archived_size"]
            else:
                initial_size = self.services[service]["archived_size"]

            # Check if there is a prior ".tar.gz" file
            # NOTE: I find dir_to_tar + ".tar.gz" easier to mentally locate the compressed files
            prompt_response = ""
            if os.path.exists(dir_to_tar + ".tar.gz"):
                stderr.print(
                    f"Seems like service {service} has already been compressed in the {location_check} dir",
                    f"Path: {dir_to_tar + '.tar.gz'}\n",
                )
                if self.skip_prompts:
                    prompt_response = (
                        f"Delete previous {service + '.tar.gz'} and compress again"
                    )
                    message = "automatically selected due to --skip-prompts"
                else:
                    message = "selected throught prompt"
                    prompt_response = buisciii.utils.prompt_selection(
                        "What to do?",
                        [
                            "Just skip it",
                            f"Delete previous {service + '.tar.gz'} and compress again",
                        ],
                    )

            try:
                if prompt_response:
                    if prompt_response.startswith("Delete"):
                        log.info(
                            f"Service {service}: compressed service {dir_to_tar + '.tar.gz'} was already found."
                            f"Option chosen is to DELETE it ({message})"
                            "Compression process will be performed again."
                        )
                        os.remove(dir_to_tar + ".tar.gz")
                    else:
                        self.services[service][
                            "compressed"
                        ] = "Found already compressed"

                if (
                    not self.services[service]["compressed"]
                    == "Found already compressed"
                ):
                    stderr.print(f"Compressing service {service}")
                    buisciii.utils.targz_dir(dir_to_tar + ".tar.gz", dir_to_tar)
                    self.services[service]["compressed"] = "Successfully compressed"

            except Exception as e:
                stderr.print(
                    f"Compression of service {service} had an error and couldnt be ended."
                    "Deleting compressed file and skipping to the next one\n."
                    f"{e}"
                )

                if os.path.exists(dir_to_tar + ".tar.gz"):
                    os.remove(dir_to_tar + ".tar.gz")

                log.info(
                    f"Service {service}: when compressing, a {e} error arised. Ending compression,"
                    "deleting compressed file and skipping to the next service."
                )
                self.services[service][
                    "error_status"
                ] = f"Error while compressing the directory: {e}"

                continue

            compressed_size = os.path.getsize(dir_to_tar + ".tar.gz") / pow(1024, 3)

            if direction == "archive":
                self.services[service]["non_archived_compressed_size"] = compressed_size
            else:
                self.services[service]["archived_compressed_size"] = compressed_size

            total_initial_size += initial_size
            total_compressed_size += compressed_size

            stderr.print(
                f"Service {service} is compressed into {dir_to_tar + '.tar.gz'}"
            )
            log.info(
                f"Service {service}: compression into {dir_to_tar + '.tar.gz'} successful."
                f"Initial size: {initial_size:.3f} GB. Compressed size: {compressed_size:.3f} GB."
                f"Saved space: {initial_size - compressed_size:.3f} GB."
            )

        # General revision of the compression process
        newly_compressed_services = [
            service
            for service in self.services.keys()
            if self.services[service]["compressed"] == "Successfully compressed"
        ]
        already_compressed_services = [
            service
            for service in self.services.keys()
            if self.services[service]["compressed"] == "Found already compressed"
        ]

        stderr.print("Compression finished")
        stderr.print(
            f"Compressed {len(newly_compressed_services + already_compressed_services)} services "
            f"({len(newly_compressed_services)} newly compressed,"
            f"{len(already_compressed_services)} already compressed)"
        )
        stderr.print(f"Total initial size: {total_initial_size:.3f} GB")
        stderr.print(f"Total compressed size: {total_compressed_size:.3f} GB")
        stderr.print(
            f"Saved space: {total_initial_size - total_compressed_size:.3f} GB"
        )
        stderr.print(
            f"Newly compressed services: {', '.join(newly_compressed_services)}"
        )
        stderr.print(
            f"Already compressed services: {', '.join(already_compressed_services)}"
        )

        log.info(
            f"Compression progress for {direction} finished:"
            f"{len(newly_compressed_services + already_compressed_services)} services were compressed "
            f"({len(newly_compressed_services)} newly compressed, "
            f"{len(already_compressed_services)} already compressed)"
            f"Total initial size: {total_initial_size:.3f} GB. "
            f"Total compressed size: {total_compressed_size:.3f} GB. "
            f"Saved space: {total_initial_size - total_compressed_size:.3f} GB."
        )
        log.info(f"Newly compressed services: {', '.join(newly_compressed_services)}")
        log.info(
            f"Already compressed services: {', '.join(already_compressed_services)}"
        )
        log.info(
            f"FINISHED: Compression of services in the"
            f" {('Archive' if direction == 'archive' else 'Data')} dir for {direction}."
        )

        return

    def sync_directory(self, direction):
        """
        Move chosen services from a place to another depending on the direction chosen:
            direction = "archive": move service from "non_archived" to "archived"
            direction = "retrieve": move service from "archived" to "non_archived"
        Make sure they are '.tar.gz' files
        """
        log.info(
            f"STARTING: Compressed service copy "
            f"({('Data dir to Archive' if direction == 'archive' else 'Archive to Data dir' )})"
        )

        for service in self.services.keys():
            # check if errors, skip
            location_check = "Data dir" if direction == "archive" else "Archive"
            if (
                location_check not in self.services[service]["found"]
                or self.services[service]["error_status"] != "No errors detected"
            ):
                log.info(
                    f"Service {service}: not found on the '{location_check}' directory or has errors. Skipping."
                )
                continue

            (origin, destiny) = (
                (
                    self.services[service]["non_archived_path"],
                    self.services[service]["archived_path"],
                )
                if direction == "archive"
                else (
                    self.services[service]["archived_path"],
                    self.services[service]["non_archived_path"],
                )
            )

            if not (os.path.exists(origin + ".tar.gz")):
                stderr.print(
                    f"{origin.split('/')[-1] + 'tar.gz'} was not found "
                    f"in the origin directory ({'/'.join(origin.split('/')[:-1])}"
                )

                self.services[service][
                    "error_status"
                ] = "Compressed directory not found"

                prompt_response = ""
                if self.skip_prompts:
                    stderr.print(
                        f"Skipping service {service} automatically (option skip-prompts activated)"
                    )
                    log.info(
                        f"Service {service}: compressed file {origin + '.tar.gz'} was not found. "
                        "Skipped automatically (option skip-prompts activated)."
                    )
                    continue
                else:
                    prompt_response = buisciii.utils.prompt_selection(
                        "What to do", ["Skip it", "Exit"]
                    )
                    if prompt_response == "Skip it":
                        stderr.print(f"Skipping service {service}")
                        log.info(
                            f"Service {service}: compressed file {origin + '.tar.gz'} was not found. "
                            "Skipped by user through prompt."
                        )
                        continue
                    else:
                        stderr.print("Exiting")
                        log.info(
                            f"Execution ended by user through prompt after service {service} "
                            f"compressed {origin + '.tar.gz'} "
                            f"file was not found in the {direction} process."
                        )
                        sys.exit(0)

            # If compressed destiny exists
            prompt_response = ""
            if os.path.exists(destiny + ".tar.gz"):
                stderr.print(
                    f"Seems like service ({service}) has already been {direction + 'd'}."
                )
                if self.skip_prompts:
                    prompt_response = f"Remove it and {direction} it again"
                    message = "(automatically option skip-prompts activated)"
                else:
                    prompt_response = buisciii.utils.prompt_selection(
                        "What to do?",
                        [f"Remove it and {direction} it again", "Ignore this service"],
                    )
                    message = "(remove option selected throught prompt)"

                if "Remove" in prompt_response:
                    stderr.print(
                        f"Removing {destiny + '.tar.gz'} automatically {message}."
                    )
                    log.info(
                        f"Service {service}: already found in {destiny + '.tar.gz'}."
                        f"File removed {message}, with intention to be copied again."
                    )
                    os.remove(destiny + ".tar.gz")
                else:
                    log.info(
                        f"Service {service}: already found in {destiny + '.tar.gz'}. "
                        "Transference skipped by user through prompt."
                    )
                    self.services[service][
                        "error_status"
                    ] = "Compressed directory found in destiny. Skipped."
                    continue

            origin_md5 = buisciii.utils.get_md5(origin + ".tar.gz")

            # save origin md5
            if direction == "archive":
                self.services[service]["md5_non_archived"] = origin_md5
            else:
                self.services[service]["md5_archived"] = origin_md5

            try:
                sysrsync.run(
                    source=origin + ".tar.gz",
                    destination=destiny + ".tar.gz",
                    options=self.conf["options"],
                    sync_source_contents=False,
                )
                destiny_md5 = buisciii.utils.get_md5(destiny + ".tar.gz")

                # save destiny md5
                if direction == "archive":
                    self.services[service]["md5_archived"] = destiny_md5
                else:
                    self.services[service]["md5_non_archived"] = destiny_md5

                # compare md5
                if origin_md5 == destiny_md5:
                    stderr.print(
                        f"[green] Service {service}: Data copied successfully from its origin folder ({origin}) "
                        f"to its destiny folder ({destiny}) (MD5: {origin_md5}; identical in both sides)",
                        highlight=False,
                    )
                    log.info(
                        f"Service {service}: copied successfully from {origin}.tar.gz to {destiny}.tar.gz."
                        f" MD5: {origin_md5}, identical in both sides.)"
                    )
                    self.services[service][
                        "copied"
                    ] = f"Successfully copied (direction: {direction}), with matching MD5"
                    os.remove(origin + ".tar.gz")
                    log.info(f"Service {service}: deleted {origin}.tar.gz")
                else:
                    stderr.print(
                        f"[red] ERROR: Service {service}: Data copied from its origin folder ({origin}) "
                        f"to its destiny folder ({destiny}), but MD5 did not match (Origin MD5: {origin_md5}; "
                        f"Destiny MD5: {destiny_md5})."
                    )
                    log.info(
                        f"Service {service}: data copied from its origin folder ({origin}) to its "
                        f"destiny folder ({destiny}), but MD5 did not match "
                        f"(Origin MD5: {origin_md5}; Destiny MD5: {destiny_md5})."
                    )

                    self.services[service][
                        "copied"
                    ] = f"Copied (direction: {direction}), MD5 NOT MATCHING."

                    self.services[service][
                        "error_status"
                    ] = "Copy error md5sum not matching"
                    os.remove(destiny + ".tar.gz")
                    log.info(f"Service {service}: deleted {destiny}.tar.gz")

            except Exception as e:
                stderr.print(
                    f"[red] ERROR: {origin.split('/')[-1] + '.tar.gz'} "
                    f"could not be copied to its destiny archive folder, {destiny}.",
                    highlight=False,
                )
                log.error(
                    f"Directory {origin} could not be archived to {destiny}.Reason: {e}"
                )

        log.info(
            f"FINISHED: Compressed service movement "
            f"({('Data dir to Archive' if direction == 'archive' else 'Archive to Data dir' )})"
        )
        return

    def uncompress_targz_directory(self, direction):
        """
        Uncompress chosen services
            When archiving, you untar to archived_path
            When retrieving, you untar to non_archived_path
        """

        log.info(
            f"STARTING: Uncompressing services"
            f"{('to Data dir for retrieval' if direction == 'retrieve' else 'to Archive dir for archive')}"
        )
        already_uncompressed_services = []
        not_found_compressed_services = []
        successfully_uncompressed_services = []

        for service in self.services.keys():
            # check if errors, skip
            location_check = "Data dir" if direction == "archive" else "Archive"
            if (
                location_check not in self.services[service]["found"]
                or self.services[service]["error_status"] != "No errors detected"
            ):
                log.info(
                    f"Service {service}: not found on the '{location_check}' directory or has errors. Skipping."
                )
                continue

            dir_to_untar = (
                self.services[service]["archived_path"]
                if (direction == "archive")
                else self.services[service]["non_archived_path"]
            )

            # Check whether the compressed file is not there
            if not os.path.exists(dir_to_untar + ".tar.gz"):
                stderr.print(
                    f"The compressed service { service + '.tar.gz'} could not be found"
                )
                log.info(
                    f"Service {service}: not uncompressed because compressed file was not found."
                    "Uncompressed service was found."
                )
                not_found_compressed_services.append(service)

                self.services[service][
                    "uncompressed"
                ] = "Could not be uncompressed, compressed file not found on destiny "
                self.services[service][
                    "error_status"
                ] = "Error uncompressing, compressed file not found."

                continue
            # Compressed file is there
            else:
                if os.path.exists(dir_to_untar):
                    stderr.print(
                        f"Service {service} is already uncompressed in the destiny"
                        f"folder {'/'.join(dir_to_untar.split('/')[:-1])[:-1]}"
                    )

                    prompt_response = ""
                    if self.skip_prompts:
                        prompt_response = (
                            f"Delete uncompressed {service} and uncompress again"
                        )
                        message = (
                            "(automatically delete and uncompress, --skip-prompts)"
                        )
                    else:
                        prompt_response = buisciii.utils.prompt_selection(
                            "What to do?",
                            [
                                "Skip (dont uncompress)",
                                f"Delete uncompressed {service} and uncompress again",
                            ],
                        )
                        message = "(delete and uncompress selected throught prompt)"

                    if prompt_response.startswith("Delete"):
                        stderr.print(
                            f"Deleting uncompressed service {service} automatically"
                            f"{message}"
                        )
                        log.info(
                            f"Service {service}: service was already found uncompressed in the destiny"
                            f"folder {dir_to_untar}. Delete the uncompressed service automatically"
                            f" {message} to uncompress it again."
                        )
                        shutil.rmtree(dir_to_untar)
                        stderr.print("Deleted!")
                    else:
                        already_uncompressed_services.append(service)
                        self.services[service][
                            "uncompressed"
                        ] = "Was not uncompressed due to the presence of a previously uncompressed directory"
                        log.info(
                            f"Service {service}: service was already found uncompressed in the destiny "
                            f"folder {dir_to_untar}. User decided to skip uncompression {message}"
                        )
                        continue

                stderr.print(f"Uncompressing {dir_to_untar.split('/')[-1] + '.tar.gz'}")

                buisciii.utils.uncompress_targz_directory(
                    dir_to_untar + ".tar.gz", dir_to_untar
                )

                stderr.print(f"Service {service} has been successfully uncompressed")
                log.info(f"Service {service}: successfully uncompressed")
                os.remove(dir_to_untar + ".tar.gz")
                log.info(f"Service {service}: deleted {dir_to_untar}.tar.gz")
                self.services[service]["uncompressed"] = "Uncompressed successfully"
                successfully_uncompressed_services.append(service)

        stderr.print(
            f"Uncompressed services: {len(successfully_uncompressed_services)}: "
            f"{', '.join(successfully_uncompressed_services)}."
        )
        log.info(
            f"Uncompressed services: {len(successfully_uncompressed_services)}: "
            f"{', '.join(successfully_uncompressed_services)}."
        )

        if len(already_uncompressed_services) > 0:
            stderr.print(
                f"The following {len(already_uncompressed_services)} service directories were found compressed already:"
                f"{', '.join(already_uncompressed_services)}"
            )
            log.info(
                f"The following {len(already_uncompressed_services)} service directories were found compressed already:"
                f"{', '.join(already_uncompressed_services)}"
            )

        if len(not_found_compressed_services) > 0:
            stderr.print(
                f"The following {len(not_found_compressed_services)} services could not be uncompressed "
                f"because the compressed service could not be found: {', '.join(not_found_compressed_services)}"
            )
            log.info(
                f"The following {len(not_found_compressed_services)} services could not be uncompressed "
                f"because the compressed service could not be found: {', '.join(not_found_compressed_services)}"
            )

        log.info(
            "FINISHED: Uncompressing services for "
            f"{('to Data dir for retrieval' if direction == 'retrieve' else 'to Archive dir for archive')}"
        )
        return

    def delete_non_archived_dirs(self):
        """
        Check that the archived counterpart exists
        Delete the non-archived copy
        NOTE: archived_path should NEVER have to be deleted
        """

        for service in self.services.keys():
            if not os.path.exists(self.services[service]["non_archived_path"]):
                stderr.print(
                    f"Service {self.services[service]['non_archived_path'].split('/')[-1]}"
                    "has already been removed from"
                    f"{'/'.join(self.services[service]['non_archived_path'].split('/')[:-1])[:-1]}."
                    "Nothing to delete so skipping.\n"
                )
                log.info(
                    f"Service {self.services[service]['non_archived_path'].split('/')[-1]} "
                    "has already been removed from"
                    f"{'/'.join(self.services[service]['non_archived_path'].split('/')[:-1])[:-1]}."
                    "Nothing to delete so skipping.\n"
                )
                continue
            else:
                if not os.path.exists(self.services[service]["archived_path"]):
                    stderr.print(
                        f"Archived path for service {self.services[service]['archived_path'].split('/')[-1]}"
                        " does NOT exist. Skipping.\n"
                    )
                    log.info(
                        f"Archived path for service {self.services[service]['archived_path'].split('/')[-1]}"
                        " does NOT exist. Skipping.\n"
                    )
                else:
                    stderr.print(
                        f"Found archived path for service {self.services[service]['archived_path'].split('/')[-1]}."
                        "It is safe to delete this non_archived service. Deleting.\n"
                    )
                    log.info(
                        f"Found archived path for service {self.services[service]['archived_path'].split('/')[-1]}."
                        "It is safe to delete this non_archived service. Deleting.\n"
                    )
                    shutil.rmtree(self.services[service]["non_archived_path"])
        return

    def generate_tsv_table(self, filename):
        """
        Create a csv file containing the info for each service
        """

        if os.path.exists(filename):
            new_filename = filename.split(".")[0] + ".1.tsv"
            stderr.print(
                f"A tsv file named {filename} has already been found. Changing name to {new_filename}."
            )
            log.info(
                f"A tsv file named {filename} has already been found. Name changed to {new_filename}."
            )
            filename = new_filename
        else:
            stderr.print(f"Generating TSV table to: {filename}")
            log.info(f"STARTING: Generation of TSV table to: {filename}")

        with open(filename, "w") as infile:
            csv_dict = {
                "Service ID": None,
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
                "Error": None,
            }

            infile.write("\t".join(list(csv_dict.keys())) + "\n")

            for service in self.services.keys():
                csv_dict["Service ID"] = service
                csv_dict["Found on iSkyLIMS"] = (
                    "Found on iSkyLIMS"
                    if self.services[service]["found_in_system"]
                    else "NOT found on iSkyLIMS"
                )
                csv_dict["Delivery date"] = self.services[service]["delivery_date"]

                # Fields for archive
                csv_dict["Path in archive"] = (
                    self.services[service]["archived_path"]
                    if self.services[service]["archived_path"] is not None
                    else "Archived path could not be generated"
                )
                csv_dict["Found on archive"] = (
                    "Yes"
                    if "Archive" in self.services[service]["found"]
                    else "Not found in archive"
                )
                csv_dict["Uncompressed size in archive"] = (
                    self.services[service]["archived_size"]
                    if self.services[service]["archived_size"] != 0
                    else "Not calculated"
                )
                csv_dict["Compressed size in archive"] = (
                    self.services[service]["archived_compressed_size"]
                    if self.services[service]["archived_compressed_size"] != 0
                    else "Not calculated"
                )
                csv_dict["Compressed md5 in archive"] = (
                    self.services[service]["md5_non_archived"]
                    if self.services[service]["md5_non_archived"] is not None
                    else "Not obtained"
                )

                # Fields for data directory
                csv_dict["Path in data directory"] = (
                    self.services[service]["non_archived_path"]
                    if self.services[service]["non_archived_path"] is not None
                    else "Data path could not be generated"
                )
                csv_dict["Found on data directory"] = (
                    "Yes"
                    if "Data dir" in self.services[service]["found"]
                    else "Not found in data dir"
                )
                csv_dict["Uncompressed size in data directory"] = (
                    self.services[service]["non_archived_size"]
                    if self.services[service]["non_archived_size"] != 0
                    else "Not calculated"
                )
                csv_dict["Compressed size in data directory"] = (
                    self.services[service]["non_archived_compressed_size"]
                    if self.services[service]["non_archived_compressed_size"] != 0
                    else "Not calculated"
                )
                csv_dict["Compressed md5 in data directory"] = (
                    self.services[service]["md5_non_archived"]
                    if self.services[service]["md5_non_archived"] is not None
                    else "Not obtained"
                )

                # Fields for processes
                csv_dict["Compressing process"] = self.services[service]["compressed"]
                csv_dict["Moving process"] = self.services[service]["copied"]
                csv_dict["Uncompressing process"] = self.services[service][
                    "uncompressed"
                ]
                csv_dict["Deletion process"] = self.services[service]["deleted"]
                csv_dict["Deletion process"] = self.services[service]["error_status"]

                infile.write(
                    "\t".join([str(item) for item in list(csv_dict.values())]) + "\n"
                )
                log.info(
                    f"Service {service} added successfully to TSV file named {filename}"
                )
        log.info(f"FINISHED: Generation of TSV table to: {filename}")

        return

    def handle_archive(self):
        """
        Handle archive class options
        """
        if self.option == "Scout for service size":
            self.scout_directory_sizes()
            self.generate_tsv_table(filename=self.output_name)

        elif self.option == "Full archive: compress and archive":
            self.scout_directory_sizes()
            self.targz_directory(direction="archive")
            self.sync_directory(direction="archive")
            self.uncompress_targz_directory(direction="archive")
            self.generate_tsv_table(filename=self.output_name)

        elif self.option.lstrip() == "Partial archive: compress NON-archived service":
            self.scout_directory_sizes()
            self.targz_directory(direction="archive")
            self.generate_tsv_table(filename=self.output_name)

        elif (
            self.option.lstrip()
            == "Partial archive: archive NON-archived service (must be compressed first) and check md5"
        ):
            self.sync_directory(direction="archive")
            self.generate_tsv_table(filename=self.output_name)

        elif (
            self.option.lstrip()
            == "Partial archive: uncompress newly archived compressed service"
        ):
            self.uncompress_targz_directory(direction="archive")
            self.generate_tsv_table(filename=self.output_name)

        elif self.option == "Full retrieve: retrieve and uncompress":
            self.targz_directory(direction="retrieve")
            self.sync_directory(direction="retrieve")
            self.uncompress_targz_directory(direction="retrieve")
            self.generate_tsv_table(filename=self.output_name)

        elif self.option.lstrip() == "Partial retrieve: compress archived service":
            self.targz_directory(direction="retrieve")
            self.generate_tsv_table(filename=self.output_name)

        elif (
            self.option.lstrip()
            == "Partial retrieve: retrieve archived service (must be compressed first) and check md5"
        ):
            self.sync_directory(direction="retrieve")
            self.generate_tsv_table(filename=self.output_name)

        elif self.option.lstrip() == "Partial retrieve: uncompress retrieved service":
            self.uncompress_targz_directory(direction="retrieve")
            self.generate_tsv_table(filename=self.output_name)

        elif (
            self.option
            == "Remove selected services from data dir (only if they are already in archive dir)"
        ):
            self.delete_non_archived_dirs()
            self.generate_tsv_table(filename=self.output_name)

        elif self.option == "That should be all, thank you!":
            sys.exit()
        return
