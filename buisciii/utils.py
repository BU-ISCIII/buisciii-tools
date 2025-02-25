#!/usr/bin/env python
import logging
import calendar
import datetime
import hashlib
import json
import os
import tarfile
import sys
import subprocess

import questionary
import rich
import yaml

import buisciii
import buisciii.config_json
import buisciii.service_json


def rich_force_colors():
    """
    Check if any environment variables are set to force Rich to use coloured output
    """
    if (
        os.getenv("GITHUB_ACTIONS")
        or os.getenv("FORCE_COLOR")
        or os.getenv("PY_COLORS")
    ):
        return True
    return None


log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True, style="dim", highlight=False, force_terminal=rich_force_colors()
)


def prompt_resolution_id():
    stderr.print(
        "Specify the name resolution id for the service you want to create."
        "You can obtain this from iSkyLIMS. eg. SRVCNM564.1"
    )
    resolution_id = questionary.text("Resolution id").unsafe_ask()
    return resolution_id


def prompt_service_id():
    stderr.print(
        "Specify the name service ID for the service you want to create."
        "You can obtain this from iSkyLIMS. eg. SRVCNM564"
    )
    resolution_id = questionary.text("Service ID").unsafe_ask()
    return resolution_id


def prompt_year(lower_limit, upper_limit):
    """
    Ask the year (user prompt)
    Check whether or not this input is a numeric value
    Check whether or not this input is within the limits
    Maybe too specific for utils
    """
    while True:
        year = questionary.text(f"Year ({lower_limit}-{upper_limit})").unsafe_ask()

        try:
            # Check if it is an int
            year = int(year)

        except ValueError:
            stderr.print(
                f"Ooops, seems like the answer '{year}' is not a year!"
                "Please specify the year for which you want to archive services."
            )

        # Check limits
        if year < lower_limit:
            stderr.print(
                f"Sorry, but the year cant be earlier than {lower_limit}!"
                "That would cause a space-time rupture and the Doctor is nowhere to be found! Please, try again!"
            )
        elif year > upper_limit:
            stderr.print(
                f"Sorry, but the time machine has not been invented... Yet. Year {year} is maybe too..."
                "Futuristic. Please, try again!"
            )
        else:
            return year

    return


def prompt_day(lower_limit, upper_limit):
    """
    Ask the day (user prompt)
    Check whether or not this input is a numeric value
    Chech whether or not this input is within the limits
    Maybe too specific for utils
    And similar to the prompt_year function (different context tho)
    """
    while True:
        day = questionary.text(f"Day ({lower_limit} - {upper_limit})").unsafe_ask()
        try:
            day = int(day)
            if day < lower_limit or day > upper_limit:
                stderr.print(
                    f"Sorry, day {day} is out of bounds! Please choose a day between {lower_limit} and {upper_limit}."
                )
            else:
                return day
        except ValueError:
            stderr.print(
                f"Ooops, seems like the answer '{day}' is not a valid day!"
                "Please specify the day for which you want to archive services (from {lower_limit} to {upper_limit})."
            )


def prompt_service_dir_path():
    stderr.print("Service path to copy to execution temporal directory")
    source = questionary.path("Source path").unsafe_ask()
    return source


def prompt_tmp_dir_path():
    stderr.print("Temporal directory destination to execute sercive")
    source = questionary.path("Source path").unsafe_ask()
    return source


def prompt_source_path():
    stderr.print("Directory containing files cd to transfer")
    source = questionary.path("Source path").unsafe_ask()
    return source


def prompt_destination_path():
    stderr.print("Directory to which the files will be transfered")
    destination = questionary.path("Destination path").unsafe_ask()
    return destination


def prompt_selection(msg, choices):
    selection = questionary.select(msg, choices=choices).unsafe_ask()
    return selection


def prompt_path(msg):
    source = questionary.path(msg).unsafe_ask()
    return source


def prompt_yn_question(msg, dflt):
    confirmation = questionary.confirm(msg, default=dflt).unsafe_ask()
    return confirmation


def prompt_skip_folder_creation():
    stderr.print("Do you want to skip folder creation? (y/N)")
    confirmation = questionary.confirm("Skip?", default=False).unsafe_ask()
    return confirmation


def get_service_ids(services_requested):
    service_id_list = []
    service_id_list_all = []
    for services in services_requested:
        if services["service_id"] is not None:
            service_id_list.append(services["service_id"])
            service_id_list_all.append(services["service_id"])
            services_json = buisciii.service_json.ServiceJson()
            try:
                service_end = services_json.get_find(services["service_id"], "end")
            except KeyError as e:
                stderr.print(
                    "[red]ERROR: Service id %s not found in services json file."
                    % services["service_id"]
                )
                stderr.print("traceback error %s" % e)
                sys.exit()
            if service_end not in service_id_list and service_end != "":
                service_id_list.append(service_end)
                service_id_list_all.append(service_end)
    service_id_list_all.append("all")
    stderr.print("Which selected service do you want to manage?")
    services_sel = [prompt_selection("Service label:", service_id_list_all)]
    if "all" in services_sel:
        services_sel = service_id_list
    return services_sel


def ask_for_some_text(msg):
    input_text = questionary.text(msg).unsafe_ask()
    return input_text


def ask_password(msg):
    password = questionary.password(msg).unsafe_ask()
    return password


def get_service_paths(conf, type, info, archived_status):
    """
    Given a service, a conf and a type,
    get the path it would have service
    """
    global_conf = conf.get_configuration("global")
    service_path = None

    try:
        if type == "services_and_colaborations":
            if archived_status == "archived_path":
                service_path = os.path.join(
                    global_conf["archived_path"],
                    type,
                    info["service_user_id"]["profile"]["profile_center"],
                    info["service_user_id"]["profile"][
                        "profile_classification_area"
                    ].lower(),
                )
            if archived_status == "non_archived_path":
                service_path = os.path.join(
                    global_conf["data_path"],
                    type,
                    info["service_user_id"]["profile"]["profile_center"],
                    info["service_user_id"]["profile"][
                        "profile_classification_area"
                    ].lower(),
                )
        return service_path

    except AttributeError:
        stderr.print(
            "[red]ERROR: the user associated with this service has no profile classification area selected in iskylims.isciii.es/admin. Please log in, go to the Profiles section and make sure every user has been assigned a profile classification area."
        )
        sys.exit(1)


def get_sftp_folder(conf, resolution_info):
    service_user = resolution_info["service_user_id"]["username"]
    json_file = os.path.join(os.path.dirname(__file__), "templates", "sftp_user.json")
    user_sftp_file = open(json_file)
    json_data = json.load(user_sftp_file)
    user_sftp_file.close()
    sftp_folders_list = []
    for user_sftp in json_data:
        if user_sftp == service_user:
            sftp_folders_list = json_data[user_sftp]
    data_path = conf.get_configuration("global")["data_path"]
    if not sftp_folders_list:
        print(f"User {service_user} does not have an assigned sftp folder. Aborting...")
        exit()
    if len(sftp_folders_list) == 1:
        sftp_folder = os.path.join(data_path, "sftp", sftp_folders_list[0])
        sftp_final_folder = sftp_folders_list[0]
    else:
        sftp_final_folder = buisciii.utils.prompt_selection(
            msg="Select SFTP folder containing the service to make tree from.",
            choices=sftp_folders_list,
        )
        sftp_folder = os.path.join(data_path, "sftp", sftp_final_folder)

    return sftp_folder, sftp_final_folder


def append_end_to_service_id_list(services_requested):
    service_ids_requested = []
    for service_id in services_requested:
        if service_id["service_id"] is not None:
            service_ids_requested.append(service_id["service_id"])
    for service_id in service_ids_requested:
        if (
            buisciii.service_json.ServiceJson().get_find(service_id, "end") != ""
            and buisciii.service_json.ServiceJson().get_find(service_id, "end")
            not in service_ids_requested
        ):
            service_ids_requested.append(
                buisciii.service_json.ServiceJson().get_find(service_id, "end")
            )

    return service_ids_requested


def get_dir_size(path):
    """
    Get the size in bytes of a given directory
    """
    size = 0

    for path, dirs, files in os.walk(path):
        for file in files:
            try:
                if os.path.islink(os.path.join(path, file)):
                    size += os.lstat(os.path.join(path, file)).st_size
                else:
                    size += os.path.getsize(os.path.join(path, file))
            except FileNotFoundError as e:
                log.warning(f"File not found error while scouting size: {e}")

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


def get_md5(file_path, chunk_size=1 * 1024 * 1024 * 1024):  # 1 GB
    """
    Given a file, open it and digest to get the md5
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


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
    year = buisciii.utils.prompt_year(
        lower_limit=lower_limit_year, upper_limit=datetime.date.today().year
    )

    # Limit the list to the current month if year = current year
    # This could be a one-liner:
    # month_list = [[num, month] for num, month in enumerate(month_name)][1:] if year < date.today().year
    # else month_list = [[num, month] for num, month in enumerate(month_name)][1:date.today().month+1]
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
        buisciii.utils.prompt_selection(
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
    day = buisciii.utils.prompt_day(
        lower_limit=int(day_list[0]), upper_limit=int(day_list[-1])
    )

    return datetime.date(int(year), int(chosen_month_number), int(day))


def get_yaml_config(conf, path):
    """Search the config yaml file described in configuration.json and extract fields

    Returns:
    -------
        yaml_fields = {
            "api_user": "User for Iskylims API" (str) ,
            "api_credentials": "Password to API user" (str) ,
            "Other keys": "values"
        }
    """
    if path:
        yaml_path = path
    else:
        yaml_path = conf.get_find("global", "yaml_conf_path")

    try:
        yaml_file = os.path.expanduser(yaml_path)
    except Exception:
        print("Yaml file path could not be resolved")
        return {}
    yaml_fields = process_yaml_file(yaml_file)
    if yaml_fields:
        return yaml_fields
    else:
        print("Could not extract fields from config file", yaml_file)
        return {}


def validate_api_credentials(cred_fields):
    """Validate that API credentials are present in dictionary

    Parameters:
    ----------
        cred_fields (dict): Dictionary containing the fields from yaml config file

    Returns:
        Bool: True if api_user and api_password are present in the dictionary
    """
    user, password = cred_fields.get("api_user"), cred_fields.get("api_password")
    if user and password:
        return True
        # This could include a test to the API to check that the credentials are correct
        """
        conf_api = buisciii.config_json.ConfigJson().get_configuration(
            "xtutatis_api_settings"
        )
        rest_api = buisciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"], user, password,
        )
        # This doesn't work, returns error 404
        status = rest_api.basic_authentication()
        return status
        """
    else:
        print("Missing credentials in yaml file given")
        return


def process_yaml_file(yaml_file):
    """Read a yaml file and return a dictionary with key/value pairs

    Args:
        yaml_file (str): Path to the file in yaml format

    Returns:
        dict: Dictionary containing the fields in the yaml file
    """
    if os.path.exists(yaml_file):
        with open(yaml_file, "r") as cred_file:
            yaml_fields = yaml.safe_load(cred_file)
        return yaml_fields
    else:
        print(f"Config file {yaml_file} does not exist")
        return


def validate_date(date_previous, date_posterior):
    return


def remake_permissions(copied_folder_path, permissions_config):
    """
    Change permissions of all files and directories in a given absolute path.

    Args:
        copied_folder_path: The path to the folder that was copied
        permissions_config: Dictionary containing permissions configuration (e.g., {'directory_chmod': '755', 'file_chmod': '664'})
    """
    subprocess.run(
        f"chown -R $(whoami):bi {copied_folder_path}", shell=True, check=True
    )

    # Change permissions for directories
    if "directory_chmod" in permissions_config:
        subprocess.run(
            f"find {copied_folder_path} -type d -exec chmod {permissions_config['directory_chmod']} {{}} \;",
            shell=True,
            check=True,
        )

    # Change permissions for files
    if "file_chmod" in permissions_config:
        subprocess.run(
            f"find {copied_folder_path} -type f -exec chmod {permissions_config['file_chmod']} {{}} \;",
            shell=True,
            check=True,
        )
