#!/usr/bin/env python
import os
import rich
import questionary
import bu_isciii
import bu_isciii.config_json
import bu_isciii.service_json
import json


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


stderr = rich.console.Console(
    stderr=True, style="dim", highlight=False, force_terminal=rich_force_colors()
)


def prompt_resolution_id():
    stderr.print(
        "Specify the name resolution id for the service you want to create. You can obtain this from iSkyLIMS. eg. SRVCNM564.1"
    )
    resolution_id = questionary.text("Resolution id").unsafe_ask()
    return resolution_id


def prompt_year():
    stderr.print("Specify the year for which you want to archive services.")
    year = questionary.text("Year").unsafe_ask()
    return year


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


def prompt_yn_question(msg):
    confirmation = questionary.confirm(msg).unsafe_ask()
    return confirmation


def prompt_skip_folder_creation():
    stderr.print("Do you want to skip folder creation? (Y/N)")
    confirmation = questionary.confirm("Skip?", default=False).unsafe_ask()
    return confirmation


def get_service_ids(services_requested):
    service_id_list = []
    service_id_list_all = []
    for services in services_requested:
        if services["serviceId"] is not None:
            service_id_list.append(services["serviceId"])
            service_id_list_all.append(services["serviceId"])
    service_id_list_all.append("all")
    stderr.print("Which selected service do you want to manage?")
    services_sel = [prompt_selection("Service label:", service_id_list_all)]
    if "all" in services_sel:
        services_sel = service_id_list
    return services_sel


def get_delivery_notes(msg):
    delivery_notes = questionary.text(msg).unsafe_ask()
    return delivery_notes


def ask_api_pass():
    stderr.print("Write API password for logging")
    api_password = questionary.password("API password: ").unsafe_ask()
    return api_password


def get_service_paths(resolution_info):
    """
    Given a service, a conf and a type,
    get the path it would have service
    """
    global_conf = bu_isciii.config_json.ConfigJson().get_configuration("global")
    service_path = os.path.join(
        global_conf["data_path"],
        "services_and_colaborations",
        resolution_info["serviceUserId"]["profile"]["profileCenter"],
        resolution_info["serviceUserId"]["profile"][
            "profileClassificationArea"
        ].lower(),
    )
    return service_path


def get_sftp_folder(resolution_info):
    service_user = resolution_info["serviceUserId"]["username"]
    json_file = os.path.join(os.path.dirname(__file__), "templates", "sftp_user.json")
    user_sftp_file = open(json_file)
    json_data = json.load(user_sftp_file)
    user_sftp_file.close()
    for user_sftp in json_data:
        if user_sftp == service_user:
            sftp_folders_list = json_data[user_sftp]
    data_path = bu_isciii.config_json.ConfigJson().get_configuration("global")[
        "data_path"
    ]
    if len(sftp_folders_list) == 1:
        sftp_folder = os.path.join(data_path, "sftp", sftp_folders_list[0])
    else:
        sftp_final_folder = bu_isciii.utils.prompt_selection(
            msg="Select SFTP folder containing the service to make tree from.",
            choices=sftp_folders_list,
        )
        sftp_folder = os.path.join(data_path, "sftp", sftp_final_folder)

    return sftp_folder, sftp_final_folder


def append_end_to_service_id_list(services_requested):
    service_ids_requested = []
    for service_id in services_requested:
        service_ids_requested.append(service_id["serviceId"])

    for service_id in service_ids_requested:
        if (
            bu_isciii.service_json.ServiceJson().get_find(service_id, "end") != ""
            and bu_isciii.service_json.ServiceJson().get_find(service_id, "end")
            not in service_ids_requested
        ):
            service_ids_requested.append(
                bu_isciii.service_json.ServiceJson().get_find(service_id, "end")
            )

    return service_ids_requested
