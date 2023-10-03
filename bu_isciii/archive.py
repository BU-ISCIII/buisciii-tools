#!/usr/bin/env python

import logging
import os
import shutil
import sys
from math import pow

import rich
import sysrsync

import bu_isciii
import bu_isciii.config_json
import bu_isciii.drylab_api
import bu_isciii.utils

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)


class Archive:
    """
    This class handles archive of active services and retrieval of archived services, from/to the
    respectives folders / repositories
    """

    def __init__(
        self,
        service_id=None,
        ser_type=None,
        option=None,
        api_token=None,
        skip_prompts=False,
        date_from=None,
        date_until=None,
    ):
        # LOG: called the archive repository
        log.info("Activated archive module of the bu-isciii tools")

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
            "moved": "No movement performed",
            "uncompressed": "No uncompression performed",
            "deleted": "No deletion performed",
            "error_status": "No errors detected",
        }

        # Get configuration params from configuration.json
        # Get data to connect to the API
        self.conf = bu_isciii.config_json.ConfigJson().get_configuration("archive")
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")

        # Initiate API
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"],
            conf_api["api_url"],
            api_token,
        )

        self.skip_prompts = skip_prompts
        self.option = option
        if ser_type is None or ser_type not in [
            "services_and_colaborations",
            "research",
        ]:
            stderr.print("Working with a service, or a research resolution?")
            self.ser_type = bu_isciii.utils.prompt_selection(
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
            (date_from is not None)
            and (date_until is not None)
            and (service_id is not None)
        ):
            stderr.print(
                "Both a date and a service ID have been chosen. Which one would you like to keep?"
            )
            prompt_response = bu_isciii.utils.prompt_selection(
                "Date or Service ID?",
                ["Search by date", "Search by ID"],
            )
            if (prompt_response) == "Search by date":
                service_id = None
            else:
                date_from = None
                date_until = None

        if (date_from is None) and (date_until is None) and (service_id is None):
            prompt_response = bu_isciii.utils.prompt_selection(
                "Search services by date, or by service ID?",
                ["Search by date", "Service ID"],
            )
            log.info("Services chosen by: " + prompt_response)
            if prompt_response == "Search by date":
                stderr.print("Please state the initial date for filtering")
                self.date_from = bu_isciii.utils.ask_date()
                stderr.print(
                    "Please state the final date for filtering (must be posterior or identical to the initial date)"
                )
                self.date_until = bu_isciii.utils.ask_date(previous_date=self.date_from)

                log.info(f"Starting date: {self.date_from} (chosen through prompt)")
                log.info(f"Ending date: {self.date_until} (chosen through prompt)")
                stderr.print(
                    f"Asking our trusty API about resolutions between: {self.date_from} and {self.date_until}"
                )
            elif prompt_response == "Service ID":
                if not self.services.keys():
                    new_service = bu_isciii.utils.prompt_service_id()
                    self.services = {
                        new_service: {
                            key: value for key, value in dictionary_template.items()
                        }
                    }
                    log.info(f"Chosen service: {new_service} (chosen through prompt)")

                # Ask if more services will be chosen
                while True:
                    prompt_response = bu_isciii.utils.prompt_selection(
                        "Would you like to add any other service?",
                        ["Add more services", "Do not add more services"],
                    )
                    if prompt_response == "Do not add more services":
                        break
                    else:
                        new_service = bu_isciii.utils.prompt_service_id()
                        self.services[new_service] = {
                            key: value for key, value in dictionary_template.items()
                        }
                        log.info(
                            f"Chosen service: {new_service} (chosen through prompt)"
                        )
        else:
            self.date_from = date_from
            self.date_until = date_until
            self.services = (
                {service_id: {key: value for key, value in dictionary_template.items()}}
                if service_id is not None
                else dict()
            )

        stderr.print(
            f"Asking our trusty API about services: {', '.join([service for service in self.services.keys()])}"
        )

        if (self.date_from is not None) and (self.date_until is not None):
            try:
                for service in rest_api.get_request(
                    request_info="services",
                    safe=False,
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
            if isinstance(
                (
                    service_data := rest_api.get_request(
                        request_info="service-data", safe=False, service=service
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
                    bu_isciii.utils.get_service_paths(
                        self.ser_type, service_data, "archived_path"
                    ),
                    service_data["resolutions"][0]["resolution_full_number"],
                )

                self.services[service]["non_archived_path"] = os.path.join(
                    bu_isciii.utils.get_service_paths(
                        self.ser_type, service_data, "non_archived_path"
                    ),
                    service_data["resolutions"][0]["resolution_full_number"],
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
                        bu_isciii.utils.prompt_selection(
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

        # Generate table with the generated info
        size_table = rich.table.Table()
        size_table.add_column("Service ID", justify="center")
        size_table.add_column("Directory size (GB)", justify="center")
        size_table.add_column("Found in", justify="center")

        for service in self.services.keys():
            if "Data dir" in self.services[service]["found"]:
                self.services[service][
                    "non_archived_size"
                ] = bu_isciii.utils.get_dir_size(
                    self.services[service]["non_archived_path"]
                ) / pow(
                    1024, 3
                )
            if "Archive" in self.services[service]["found"]:
                self.services[service]["archived_size"] = bu_isciii.utils.get_dir_size(
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
                    prompt_response = bu_isciii.utils.prompt_selection(
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
                    bu_isciii.utils.targz_dir(dir_to_tar + ".tar.gz", dir_to_tar)
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
            f"STARTING: Compressed service movement "
            f"({('Data dir to Archive' if direction == 'archive' else 'Archive to Data dir' )})"
        )

        for service in self.services.keys():
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

            # If compressed origin cannot be found
            # Check for uncompressed origin
            if not (os.path.exists(origin + ".tar.gz")):
                stderr.print(
                    f"{origin.split('/')[-1] + 'tar.gz'} was not found "
                    "in the origin directory ({'/'.join(origin.split('/')[:-1])}"
                )
                if os.path.exists(origin):
                    stderr.print(
                        f"Origin path {origin} was found. Please make sure this directory has been compressed."
                    )

                    prompt_response = bu_isciii.utils.prompt_selection(
                        "What to do", ["Skip it", "Exit"]
                    )
                    if (prompt_response == "Skip it") or (self.skip_prompts):
                        if self.skip_prompts:
                            stderr.print(
                                f"Skipping service {service} automatically (option skip-prompts activated)"
                            )
                            log.info(
                                f"Service {service}: compressed file {origin + '.tar.gz'} was not found. "
                                "Skipped automatically (option skip-prompts activated)."
                            )
                        else:
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
                            "compressed {origin + '.tar.gz'} "
                            f"file was not found in the {direction} process."
                        )
                        sys.exit(0)

                else:
                    stderr.print(
                        f"Origin path {origin} was not found either. Skipping."
                    )
                    log.info(
                        f"Service {service}: neither compressed path ({origin + '.tar.gz'}) "
                        f"or uncompressed path ({origin}) could be found. Skipping."
                    )
                    continue

            # If compresed destiny exists
            if os.path.exists(destiny + ".tar.gz"):
                stderr.print(
                    f"Seems like service ({service}) has already been {direction + 'd'}."
                )
                prompt_response = bu_isciii.utils.prompt_selection(
                    "What to do?",
                    [f"Remove it and {direction} it again", "Ignore this service"],
                )
                if ("Remove" in prompt_response) or (self.skip_prompts):
                    if self.skip_prompts:
                        stderr.print(
                            f"Removing {destiny + '.tar.gz'} automatically (option skip-prompts activated)."
                        )
                        log.info(
                            f"Service {service}: already found in {destiny + '.tar.gz'}. File removed automatically "
                            "(option skip-prompts activated), with intention to be copied again."
                        )
                    else:
                        stderr.print(
                            f"Removing {destiny + '.tar.gz'} automatically by user through prompt."
                        )
                        log.info(
                            f"Service {service}: already found in {destiny + '.tar.gz'}. "
                            "File was removed by user instruction through prompt, with intention to be copied again."
                        )

                    os.remove(destiny + ".tar.gz")
                    stderr.print("Removed successfully")
                else:
                    log.info(
                        f"Service {service}: already found in {destiny + '.tar.gz'}. "
                        "Transference skipped by user through prompt."
                    )
                    continue

            origin_md5 = bu_isciii.utils.get_md5(origin + ".tar.gz")

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
                destiny_md5 = bu_isciii.utils.get_md5(destiny + ".tar.gz")

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
                        "moved"
                    ] = f"Successfully moved (direction: {direction}), with matching MD5"
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
                        "moved"
                    ] = f"Moved (direction: {direction}), MD5 NOT MATCHING."
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
                not_found_compressed_services.append(service)

                # Check whether the uncompressed dir is already there
                if os.path.exists(dir_to_untar):
                    stderr.print(
                        f"However, this service is already uncompressed in"
                        f"the destiny folder {'/'.join(dir_to_untar.split('/')[:-1])[:-1]}"
                    )
                    self.services[service]["uncompressed"] = (
                        f"Could not be uncompressed, compressed file {service + '.tar.gz'} not found on destiny "
                        "folder {'/'.join(dir_to_untar.split('/')[:-1])[:-1]}."
                        "However, the uncompressed service was found."
                    )
                    log.info(
                        f"Service {service}: not uncompressed because compressed file was not found."
                        "Uncompressed service was found."
                    )
                    continue
                else:
                    stderr.print(
                        f"The uncompressed service, {dir_to_untar} could not be found either."
                    )
                    self.services[service]["uncompressed"] = (
                        f"Could not be uncompressed, compressed file not found on destiny "
                        f"folder ({dir_to_untar + '.tar.gz'}). The uncompressed service was not found either."
                    )
                    log.info(
                        f"Service {service}: not uncompressed because compressed file was not found."
                        "Uncompressed service was NOT found either."
                    )
                    continue

            # Compressed file is there
            else:
                if os.path.exists(dir_to_untar):
                    stderr.print(
                        f"Service {service} is already uncompressed in the destiny"
                        f"folder {'/'.join(dir_to_untar.split('/')[:-1])[:-1]}"
                    )

                    prompt_response = bu_isciii.utils.prompt_selection(
                        "What to do?",
                        [
                            "Skip (dont uncompress)",
                            f"Delete uncompressed {service} and uncompress again",
                        ],
                    )

                    if (prompt_response.startswith("Delete")) or (self.skip_prompts):
                        if self.skip_prompts:
                            stderr.print(
                                f"Deleting uncompressed service {service} automatically (option skip-prompts activated)"
                            )
                            log.info(
                                f"Service {service}: service was already found uncompressed in the destiny"
                                f"folder {dir_to_untar}. Delete the uncompressed service automatically"
                                " (option skip-prompt activated) to uncompress it again."
                            )
                        else:
                            stderr.print(
                                f"Deleting uncompressed service {service} by user choice through prompt"
                            )
                            log.info(
                                f"Service {service}: service was already found uncompressed in the destiny "
                                f"folder {dir_to_untar}."
                                "User decided to delete the uncompressed service through prompt to uncompress it again."
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
                            f"folder {dir_to_untar}. User decided to skip uncompression through prompt."
                        )
                        continue

                stderr.print(f"Uncompressing {dir_to_untar.split('/')[-1] + '.tar.gz'}")

                bu_isciii.utils.uncompress_targz_directory(
                    dir_to_untar + ".tar.gz", dir_to_untar
                )

                stderr.print(f"Service {service} has been successfully uncompressed")
                log.info(f"Service {service}: successfully uncompressed")
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
                f"Already compressed services: {len(already_uncompressed_services)}: "
                f"{', '.join(already_uncompressed_services)}"
            )

        if len(not_found_compressed_services) > 0:
            stderr.print(
                f"The following {len(not_found_compressed_services)} services could not be uncompressed "
                f"because the compressed service could not be found: {', '.join(not_found_compressed_services)}"
            )
            stderr.print(
                f"Not found compressed services: {len(not_found_compressed_services)}: "
                f"{', '.join(not_found_compressed_services)}"
            )

        log.info(
            "FINISHED: Uncompressing services for "
            f"{('to Data dir for retrieval' if direction == 'retrieve' else 'to Archive dir for archive')}"
        )
        return

    def delete_targz_dirs(self, direction):
        """
        Delete the targz dirs when the original, uncompressed service is present

        if direction = archive: origin is non-archived, and you are moving to archived
        if direction = retrieve: origin is archive, and you are moving to non-archived

        """
        deleted_services = {
            "Deleted": [],
            "None": [],
        }

        file_locations = (
            [
                [
                    service,
                    self.services[service]["non_archived_path"],
                    self.services[service]["archived_path"],
                ]
                for service in self.services.keys()
            ]
            if direction == "archive"
            else [
                [
                    service,
                    self.services[service]["archived_path"],
                    self.services[service]["non_archived_path"],
                ]
                for service in self.services.keys()
            ]
        )
        origin_folder = (
            "Data directory" if direction == "archive" else "Archive directory"
        )
        destiny_folder = (
            "Archive directory" if direction == "archive" else "Data directory"
        )

        for service, origin, destiny in file_locations:
            if (os.path.exists(origin + ".tar.gz")) and (
                os.path.exists(destiny + ".tar.gz")
            ):
                # Both compressed exist, both uncompressed exist
                if (os.path.exists(origin)) and (os.path.exists(destiny)):
                    stderr.print(
                        f"For service {service}, compressed and uncompressed directories were found in both "
                        f"{origin_folder} and {destiny_folder}. It is safe to delete the compressed files."
                    )

                    os.remove(origin + ".tar.gz")
                    os.remove(destiny + ".tar.gz")

                    log.info(
                        f"Service {service}: both compressed and uncompressed service have been found in the "
                        f"{origin_folder} and the {destiny_folder}. Compressed files deleted."
                    )
                    stderr.print(
                        f"Compressed files for service {service} (in both {origin_folder} "
                        f"and {destiny_folder}) were deleted."
                    )
                    deleted_services["Deleted"].append(service)

                elif (os.path.exists(origin)) and not (os.path.exists(destiny)):
                    stderr.print(
                        f"For service {service}, compressed directories were found in both"
                        f" the {origin_folder} and the {destiny_folder}. "
                        f"However, the uncompressed directory was NOT found on the {destiny_folder} "
                        "(therefore, the compressed file will not be deleted)."
                    )
                    stderr.print(
                        f"Therefore, it is safe to delete the compressed service in "
                        f"{origin_folder}, but not in the {destiny_folder}"
                    )

                    os.remove(origin + ".tar.gz")

                    log.info(
                        f"Service {service}: compressed directory in {origin_folder} was deleted due to presence of "
                        f"the uncompressed directory. Compressed directory in {destiny_folder} was "
                        "NOT deleted due to absence of the uncompressed directory."
                    )
                    stderr.print(
                        f"Compressed service {service} in {origin_folder} was deleted"
                    )

                elif not (os.path.exists(origin)) and (os.path.exists(destiny)):
                    stderr.print(
                        f"For service {service}, compressed directories were found in the {origin_folder} and "
                        f"the {destiny_folder}. However, the uncompressed directory was not found on "
                        f"the {origin_folder}."
                    )
                    stderr.print(
                        f"Therefore, it is NOT safe to delete the compressed service in {origin_folder}, "
                        f"but it is in the {destiny_folder}"
                    )

                    os.remove(destiny + ".tar.gz")

                    log.info(
                        f"Service {service}: compressed directory in {origin_folder} was NOT deleted due to absence of "
                        f"the uncompressed directory. Compressed directory in {destiny_folder} was deleted "
                        "due to presence of the uncompressed directory."
                    )
                    stderr.print(
                        f"Compressed service {service} in {destiny_folder} was deleted"
                    )
                else:
                    stderr.print(
                        f"For service {service}, compressed directories were found in the {origin_folder} and "
                        f"the {destiny_folder}. "
                        f"However, the uncompressed directories were not found in "
                        f"the {origin_folder} or the {destiny_folder}."
                        "Please make sure these services have been uncompressed first."
                    )
                    stderr.print(
                        f"Therefore, it is safe to delete the compressed service in {origin_folder}, but not in "
                        f"the {destiny_folder}"
                    )
                    log.info(
                        f"Service {service}: compressed directories in {origin_folder} were NOT deleted due to "
                        "absence of uncompressed directories in both sides."
                    )

            elif (os.path.exists(origin + ".tar.gz")) and not (
                os.path.exists(destiny + ".tar.gz")
            ):
                if os.path.exists(origin):
                    stderr.print(
                        f"For service {service}, the compressed directory was found in the {origin_folder}, "
                        f"but NOT in the {destiny_folder} (and therefore, it cannot be deleted). "
                        f"Uncompressed directory was found in the {origin_folder}, so it can be deleted."
                    )

                    os.remove(origin + ".tar.gz")

                    log.info(
                        f"Service {service}: compressed directory in {origin_folder} was found and deleted due to "
                        f"presence of the uncompressed directory. Compressed directory in {destiny_folder} "
                        "could not be deleted because it was not found."
                    )
                    stderr.print(
                        f"Compressed service {service} in {origin_folder} was deleted."
                    )

                else:
                    stderr.print(
                        f"For service {service}, the compressed directory was found in the {origin_folder}, but NOT in "
                        f"the {destiny_folder} (and therefore, it cannot be deleted). "
                        f"Uncompressed directory was NOT found in {origin_folder}, so it should not be deleted either."
                    )
                    log.info(
                        f"Service {service}: compressed directory in {origin_folder} was found, but NOT deleted,"
                        f" due to absence of the uncompressed directory. "
                        f"Compressed directory in {destiny_folder} could not be deleted because it was not found."
                    )
            elif not (os.path.exists(origin + ".tar.gz")) and (
                os.path.exists(destiny + ".tar.gz")
            ):
                if os.path.exists(destiny):
                    stderr.print(
                        f"For service {service}, the compressed directory was NOT found in the {origin_folder} "
                        f"(and therefore, it cannot be deleted), but it WAS FOUND in "
                        f"the {destiny_folder}. Uncompressed directory was found in the {destiny_folder}"
                        "so it can be deleted."
                    )
                    log.info(
                        f"Service {service}: compressed directory in {origin_folder} was NOT found, "
                        f"and could not be deleted. Compressed directory in {destiny_folder} was FOUND and DELETED "
                        "due to presence of the uncompressed directory."
                    )

                else:
                    stderr.print(
                        f"For service {service}, the compressed directory was NOT found in the {origin_folder} "
                        f"(and therefore, it cannot be deleted), but it WAS FOUND in the {destiny_folder}. "
                        "Uncompressed directory was NOT found in the {destiny_folder}, "
                        "so it should not be deleted either."
                    )
                    log.info(
                        f"Service {service}: compressed directory in {origin_folder} was NOT found,"
                        f" and could not be deleted. Compressed directory in {destiny_folder} was FOUND, "
                        "but NOT DELETED due to absence of the uncompressed directory."
                    )
            else:
                stderr.print(
                    f"For service {service}, NONE of the compressed directories was found "
                    "(therefore, they cannot be deleted)."
                )
                log.info(
                    f"Service {service}: neither of the compressed directories was found, "
                    "and therefore they couldnt be deleted."
                )
                deleted_services["None"].append(service)

        stderr.print(
            f"Deleted {len(deleted_services['Deleted'])} compressed services: {', '.join(deleted_services['Deleted'])}"
        )
        log.info(
            f"{len(deleted_services['Deleted'])} compressed services were deleted:"
            " {', '.join(deleted_services['Deleted'])}"
        )

        if len(deleted_services["None"]) > 0:
            stderr.print(
                f"{len(deleted_services['None'])} compressed services could not be deleted:"
                f" {', '.join(deleted_services['None'])}"
            )
            log.info(f"{len(deleted_services['None'])} services were not deleted")
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
                    f"Service {self.services[service]['non_archived_path'].split('/')[-1]} has already been removed "
                    f"from {'/'.join(self.services[service]['non_archived_path'].split('/')[:-1])[:-1]}. "
                    "Nothing to delete so skipping.\n"
                )
                continue
            else:
                if not os.path.exists(self.services[service]["archived_path"]):
                    stderr.print(
                        f"Archived path for service {self.services[service]['archived_path'].split('/')[-1]} does "
                        "NOT exist. Skipping.\n"
                    )
                else:
                    stderr.print(
                        f"Found archived path for service {self.services[service]['archived_path'].split('/')[-1]}. "
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
                csv_dict["Delivery date"] = ""

                # Fields for archive
                csv_dict["Path in archive"] = (
                    self.services[service]["archived_path"]
                    if self.services[service]["archived_path"] is not None
                    else "Archived path could not be generated"
                )
                csv_dict["Found in archive"] = (
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
                csv_dict["Compressed size in data directory"] = (
                    self.services[service]["non_archived_size"]
                    if self.services[service]["non_archived_size"] != 0
                    else "Not calculated"
                )
                csv_dict["Uncompressed size in data directory"] = (
                    self.services[service]["non_archived_compressed_size"]
                    if self.services[service]["non_archived_compressed_size"] != 0
                    else "Not calculated"
                )
                csv_dict["Compressed md5 in data dir"] = (
                    self.services[service]["md5_non_archived"]
                    if self.services[service]["md5_non_archived"] is not None
                    else "Not obtained"
                )

                # Fields for processes
                csv_dict["Compressing process"] = self.services[service]["compressed"]
                csv_dict["Moving process"] = self.services[service]["moved"]
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
            self.generate_tsv_table(filename="archive_info.tsv")

        elif self.option == "Full archive: compress and archive":
            self.scout_directory_sizes()
            self.targz_directory(direction="archive")
            self.sync_directory(direction="archive")
            self.uncompress_targz_directory(direction="archive")
            self.delete_targz_dirs(direction="archive")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif self.option.lstrip() == "Partial archive: compress NON-archived service":
            self.scout_directory_sizes()
            self.targz_directory(direction="archive")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif (
            self.option.lstrip()
            == "Partial archive: archive NON-archived service (must be compressed first) and check md5"
        ):
            self.sync_directory(direction="archive")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif (
            self.option.lstrip()
            == "Partial archive: uncompress newly archived compressed service"
        ):
            self.uncompress_targz_directory(direction="archive")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif (
            self.option.lstrip()
            == "Partial archive: remove compressed services from directories"
        ):
            self.delete_targz_dirs(direction="archive")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif self.option == "Full retrieve: retrieve and uncompress":
            self.targz_directory(direction="retrieve")
            self.sync_directory(direction="retrieve")
            self.uncompress_targz_directory(direction="retrieve")
            self.delete_targz_dirs(direction="retrieve")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif self.option.lstrip() == "Partial retrieve: compress archived service":
            self.targz_directory(direction="retrieve")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif (
            self.option.lstrip()
            == "Partial retrieve: retrieve archived service (must be compressed first) and check md5"
        ):
            self.sync_directory(direction="retrieve")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif self.option.lstrip() == "Partial retrieve: uncompress retrieved service":
            self.uncompress_targz_directory(direction="retrieve")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif (
            self.option.lstrip()
            == "Partial retrieve: remove compressed services from directories"
        ):
            self.delete_targz_dirs(direction="retrieve")
            self.generate_tsv_table(filename="archive_info.tsv")

        elif (
            self.option
            == "Remove selected services from data dir (only if they are already in archive dir)"
        ):
            self.delete_non_archived_dirs()
            self.generate_tsv_table(filename="archive_info.tsv")

        elif self.option == "That should be all, thank you!":
            sys.exit()
        return
