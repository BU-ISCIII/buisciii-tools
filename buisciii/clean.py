#!/usr/bin/env python

# Generic imports
import sys
import os
import logging
import shutil
import subprocess
from pathlib import Path
from rich.console import Console

# Local imports
import buisciii
import buisciii.utils
import buisciii.drylab_api
import buisciii.service_json

log = logging.getLogger(__name__)

stderr = Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


class CleanUp:
    def __init__(
        self,
        resolution_id=None,
        path=None,
        ask_path=False,
        option=None,
        api_user=None,
        api_password=None,
        conf=None,
    ):
        # Access the API with the resolution name to obtain the data
        if resolution_id is None:
            self.resolution_id = buisciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id

        # Obtain info from iSkyLIMS API
        self.conf = conf.get_configuration("cleanning")
        conf_api = conf.get_configuration("xtutatis_api_settings")
        rest_api = buisciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"], api_user, api_password
        )
        self.resolution_info = rest_api.get_request(
            request_info="service-data", safe=True, resolution=self.resolution_id
        )
        self.service_folder = self.resolution_info["resolutions"][0][
            "resolution_full_number"
        ]
        self.services_requested = self.resolution_info["resolutions"][0][
            "available_services"
        ]
        self.service_samples = [
            sample_id["sample_name"] for sample_id in self.resolution_info["samples"]
        ]

        if ask_path and path is None:
            stderr.print(
                "Absolute path to the directory containing the service to clean."
            )
            self.path = buisciii.utils.prompt_path(msg="Path")
        elif path == "-a":
            log.error(
                "ERROR: Either give a path or make the terminal ask you for a path, not both"
            )
            stderr.print(
                "[red] ERROR: Either give a path or make the terminal ask you for a path, not both."
            )
            raise ValueError(
                "Either give a path or make the terminal ask you for a path, not both"
            )
        elif path is not None and ask_path is False:
            self.path = path
        elif path is not None and ask_path is not False:
            log.error(
                "ERROR: Either give a path or make the terminal ask you for a path, not both"
            )
            stderr.print(
                "[red] ERROR: Either give a path or make the terminal ask you for a path, not both."
            )
            raise ValueError(
                "Either give a path or make the terminal ask you for a path, not both"
            )
        else:
            self.path = buisciii.utils.get_service_paths(
                conf,
                "services_and_colaborations",
                self.resolution_info,
                "non_archived_path",
            )

        self.full_path = os.path.join(self.path, self.service_folder)
        self.scratch_path = None

        self.services_to_clean = buisciii.utils.get_service_ids(self.services_requested)
        service_conf_all = buisciii.service_json.ServiceJson()
        self.clean_scripts = {}

        for svc in self.services_to_clean:
            script = service_conf_all.get_find_deep(svc, "clean_script")
            if script:
                self.clean_scripts[svc] = script
                log.info(f"clean_script for {svc} = {script}")

        if self.clean_scripts:
            scratch_base = "/data/ucct/bi/scratch_tmp/bi"
            scratch_path = os.path.join(scratch_base, self.service_folder)
            if os.path.exists(scratch_path):
                self.scratch_path = scratch_path
                stderr.print(f"Using the following route: {self.scratch_path}")
                log.info(f"Using the following route: {self.scratch_path}")
            else:
                stderr.print(f"Scratch path was not found: {scratch_path}. The service path will be used instead: {self.full_path}")
                log.warning(f"Scratch path not found: {scratch_path}, using service path")

        self.delete_folders = self.get_clean_items(
            self.services_to_clean, type="folders"
        )
        self.delete_files = self.get_clean_items(self.services_to_clean, type="files")
        # self.delete_list = [item for item in self.delete_list if item]
        self.nocopy = self.get_clean_items(self.services_to_clean, type="no_copy")

        if option is None:
            self.option = buisciii.utils.prompt_selection(
                "Options",
                [
                    "full_clean",
                    "rename",
                    "clean",
                    "revert_renaming",
                    "show_removable",
                    "show_nocopy",
                ],
            )
        else:
            self.option = option

    def get_files_from_clean_script(self, script, search_path):
        script_path = Path(__file__).parent / "assets" / "utils" / script
        if not script_path.exists():
            log.warning(f"Clean script '{script}' not found in {script_path}")
            return []
        cmd = [sys.executable, str(script_path), search_path]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=None, text=True, check=False)
            if result.returncode == 0:
                files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                existing_files = [f for f in files if os.path.exists(f)]
                if len(existing_files) != len(files):
                    missing = set(files) - set(existing_files)
                    log.warning(f"Some files from '{script}' do not exist: {missing}")
                return existing_files
            else:
                log.error(f"Error in clean script '{script}' (code {result.returncode})")
        except Exception as e:
            log.exception(f"Failed to execute clean script '{script}': {e}")
        return []

    def get_clean_items(self, services_ids, type="files"):
        """
        Description:
            Get delete files list from service conf.

        Usage:
            object.get_delete_files(services_ids, type = "files")

        Params:
            services_ids [list]: list with services IDs selected.
            type [string]: one of these: "files", "folders" or "no_copy" for getting the param from service.json
        """
        service_conf = buisciii.service_json.ServiceJson()
        clean_items_list = []
        for service in services_ids:
            try:
                items = service_conf.get_find_deep(service, type)
                if items is None:
                    stderr.print(
                        "[red]ERROR: Service type %s not found in the services.json file for service %s."
                        % (type, service)
                    )
                    log.error(
                        f"ERROR: Service type {type} not found in the services.json file for service {service}!"
                    )
                    raise
                else:
                    for item in items:
                        if item not in clean_items_list:
                            clean_items_list.append(item)
            except KeyError:
                stderr.print(
                    "[red]ERROR: Service ID %s not found in the services.json file."
                    % service
                )
                log.error(
                    f"ERROR: Service ID {service} not found in the services.json file."
                )
                raise
        if len(clean_items_list) == 0:
            clean_items_list = ""
        return clean_items_list

    def check_path_exists(self):
        """
        Description:
            Checks if the folder path exists and, if not, exits.

        Usage:
            object.check_path_exists()

        Params:

        """
        # If the folder path is not found, then bye!
        if not os.path.exists(self.full_path):
            stderr.print(
                "[red] ERROR: It seems like finding the correct path is beneath me. I apologise. The path: %s does not exist. Exiting!"
                % self.full_path
            )
            log.error(
                f"ERROR: It seems like finding the correct path is beneath me. I apologise. The path: {self.full_path} does not exist. Exiting!"
            )
            raise

    def show_removable(self, to_stdout=True):
        """
        Description:
            Print or return the list of objects that must be deleted in this service.

        Usage:
            object.show_removable_dirs(to_stdout = [BOOL])

        Params:
            to_stdout [BOOL]: if True, print the list. If False, return the list.
        """
        if to_stdout:
            folders = ", ".join(self.delete_folders)
            stderr.print(f"The following folders will be purged: {folders}")
            log.info(f"The following folders will be purged: {folders}")
            files = ", ".join(self.delete_files)
            stderr.print(f"The following files will be deleted: {files}")
            log.info(f"The following files will be deleted: {files}")
            return
        else:
            return self.delete_folders + self.delete_files

    def show_nocopy(self, to_stdout=True):
        """
        Description:
            Print or return the list of objects that must be renamed in this service.

        Usage:
            object.show_nocopy(to_stdout = [BOOL])

        Params:
            to_stdout [BOOL]: if True, print the list. If False, return the list.
        """
        if to_stdout:
            no_copy = ", ".join(self.nocopy)
            stderr.print(f"The following files will be renamed with _NC: {no_copy}")
            log.info(f"The following files will be renamed with _NC: {no_copy}")
            return
        else:
            return self.nocopy

    def scan_dirs(self, to_find):
        """
        Description:
            Parses the directory tree, and generates two lists:
                -list with the elements (dirs and files) to be deleted
                -list with the dirs to be renamed

        If a list is given as argument, the names included
        (either files or directories) won't be added into the
        dictionary.

        Usage:
            to_rename, to_delete = object.scan_dirs(to_find=list)

        Params:

        """
        self.check_path_exists()
        search_path = self.scratch_path if self.scratch_path else self.full_path
        pathlist = []
        found = []

        for item_to_find in to_find:
            # If there are subpaths in to_find, split them into different components (e.g., ["virus_coverage", "plots"], from virus_coverage/plots)
            path_parts = item_to_find.split(os.sep)
            target_name = path_parts[-1]
            parent_dirs = path_parts[:-1]

            for root, dirs, files in os.walk(search_path):
                if root.endswith(os.sep.join(parent_dirs)):
                    # Check for matching directories, if any
                    if target_name in dirs:
                        full_path = os.path.join(root, target_name)
                        pathlist.append(full_path)
                        found.append(item_to_find)
                    # Check for matching files, if any
                    if target_name in files:
                        full_path = os.path.join(root, target_name)
                        pathlist.append(full_path)
                        found.append(item_to_find)

        # Check found list without duplicates
        if not sorted(list(dict.fromkeys(found))) == sorted(to_find):
            for item in to_find:
                if item not in found:
                    stderr.print(
                        f"[yellow]WARNING: The following item was not found: {item}"
                    )
                    log.warning(f"WARNING: The following item was not found: {item}")
        return pathlist

    def find_work(self):
        """
        Description:
            Parses the directory tree to find work folder.

        Usage:
            to_delete = object.find_work()

        Params:

        """
        self.check_path_exists()
        workdirs = []
        # key: root, values: [[files inside], [dirs inside]]
        for root, dirs, files in os.walk(self.full_path):
            for name in dirs:
                if name == "work":
                    if os.path.exists(os.path.join(root, name)):
                        workdir = os.path.join(root, name)
                        workdirs.append(workdir)
        return workdirs

    def rename(self, to_find, add, verbose=True):
        """
        Description:
            Rename the files and directories.

        Usage:
            rename(to_find=["dir1", "dir2"], add="_NC", verbose=True)

        Params:
            to_find (list[str]): List of directory names to search for inside ``self.full_path``.
            add (str): String to append to each matching directory name (e.g. "_NC").
            verbose (bool, optional): If True, prints a message for each successfully renamed directory.
        """
        # Generate the list of items to add the "_NC" to
        elements = ", ".join(to_find)
        stderr.print(f"The following directories will be renamed: {elements}")
        log.info(f"The following directories will be renamed: {elements}")
        if not buisciii.utils.prompt_yn_question("Is it okay?", dflt=True):
            stderr.print("No directories renamed!")
            log.info("No directories renamed!")
            sys.exit()

        path_content = self.scan_dirs(to_find=to_find)
        unfiltered_path_content = [f.path for f in os.scandir(self.full_path)]
        for directory_to_rename in path_content:
            renamed_directory = str(directory_to_rename + add)
            if renamed_directory in unfiltered_path_content:
                stderr.print(
                    "[orange]WARNING: Directory %s already renamed to %s Omitting..."
                    % (directory_to_rename, renamed_directory)
                )
                log.warning(
                    f"WARNING: Directory {directory_to_rename} already renamed to {renamed_directory}! Omitting..."
                )
                continue
            else:
                newpath = directory_to_rename + add
                try:
                    os.replace(directory_to_rename, newpath)
                    if verbose:
                        print(f"Renamed {directory_to_rename} to {newpath}.")
                except PermissionError:
                    stderr.print(
                        f"[red]Error moving {directory_to_rename} to {newpath}!"
                    )
                    log.info(f"Error moving {directory_to_rename} to {newpath}!")
                    raise
        return

    def purge_files(self):
        """
        Description:
            Remove the files that must be deleted before the service delivery.

        Usage:
            object.purge_files()

        Params:
        """
        if self.clean_scripts:
            search_path = self.scratch_path if self.scratch_path else self.full_path
            for svc, script in self.clean_scripts.items():
                files_to_delete = self.get_files_from_clean_script(script, search_path)
                if not files_to_delete:
                    stderr.print(f"[yellow]WARNING: No files to delete from {svc}! Let's keep going!")
                    log.info(f"No files to delete from {svc}. Continuing!")
                    continue
                for file in files_to_delete:
                    try:
                        os.remove(file)
                        stderr.print("[green]Successfully removed " + file)
                        log.info(f"Successfully removed {file}!")
                    except Exception as e:
                        stderr.print(f"[red]Error removing {file}: {e}")
                        log.error(f"Error removing {file}: {e}")
        
        services_without_script = [s for s in self.services_to_clean if s not in self.clean_scripts]
        if services_without_script and self.delete_files and self.service_samples:
            files_to_delete = []
            for sample_info in self.service_samples:
                for file in self.delete_files:
                    file_to_delete = file.replace("sample_name", sample_info)
                    if file_to_delete not in files_to_delete:
                        files_to_delete.append(file_to_delete)
            path_content = self.scan_dirs(to_find=files_to_delete)
            for file in path_content:
                try:
                    os.remove(file)
                    stderr.print("[green]Successfully removed " + file)
                    log.info(f"Successfully removed {file}!")
                except Exception as e:
                    stderr.print(f"[red]Error removing {file}: {e}")
                    log.error(f"Error removing {file}: {e}")

    def purge_folders(self, sacredtexts=["lablog", "logs"], add="", verbose=True):
        """
        Description:
            Remove the files that must be deleted for the delivery of the service.
            Their content, except for the lablog file, as well as the logs dir, will be
            deleted.

        Usage:
            object.purge_folders()

        Params:
            sacredtexts [list]: names (str) of the files that will not be deleted.

        """
        path_content = self.scan_dirs(to_find=self.delete_folders)

        for directory in path_content:
            # if not empty, and not previously DEL add it to the content
            if not directory.endswith(add):
                for item in os.listdir(directory):
                    if item not in sacredtexts:
                        item_path = os.path.join(directory, item)
                        # shutil if dir, os.remove if file
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                        if verbose:
                            stderr.print("[green]Successfully removed " + item_path)
                            log.info(f"Successfully removed {item_path}!")
        return

    def delete_work(self):
        """
        Description:
            Removes the whole work folder.

        Usage:
            object.delete_work()

        Params:

        """
        work_dir = self.find_work()
        if work_dir:
            for work_folder in work_dir:
                shutil.rmtree(work_folder)
                stderr.print("[green]Successfully removed " + work_folder)
                log.info(f"Successfully removed {work_folder}!")
        else:
            stderr.print("There is no work folder!")
            log.warning("There is no work folder!")

    def delete(self, verbose=True, sacredtexts=["lablog", "logs"], add="_DEL"):
        """
        Description:
            Remove both files and purge folders defined for the service, and rename to tag.

        Usage:
            object.delete()

        Params:

        """
        # Show removable items
        self.show_removable()

        # Ask for confirmation
        if not buisciii.utils.prompt_yn_question("Is it okay?", dflt=True):
            stderr.print("Nothing will be deleted!")
            log.info("Nothing will be deleted!")
            sys.exit()

        # Purge folders
        if self.delete_folders != "":
            self.purge_folders(sacredtexts=sacredtexts, add=add, verbose=verbose)
        else:
            stderr.print("There are no folders to delete!")
            log.info("There are no folders to delete!")

        # Purge work
        self.delete_work()
        # Delete files
        if self.clean_scripts or self.delete_files:
            self.purge_files()
        else:
            stderr.print("No files to remove!")
            log.info("No files to remove!")

    def revert_renaming(self, verbose=True, terminations=["_DEL", "_NC"]):
        """
        Description:
            Reverts the naming (adding of the _NC tag).

        """
        to_rename = self.scan_dirs(to_find=terminations)
        if not to_rename:
            stderr.print("[yellow] WARNING: I have nothing to revert renaming from!")
            log.warning("WARNING: I have nothing to revert renaming from!")
            return
        for dir_to_rename in to_rename:
            # remove all the terminations
            for term in terminations:
                if dir_to_rename.endswith(term):
                    newname = dir_to_rename.replace(term, "")
                    os.replace(dir_to_rename, newname)
            if verbose:
                stderr.print(f"Replaced {dir_to_rename} with {newname}.")
                log.info(f"Replaced {dir_to_rename} with {newname}.")

    def full_clean(self):
        """
        Description:
            Perform and handle the whole cleaning of the service.
        """

        self.delete()
        self.rename(to_find=self.nocopy, add="_NC", verbose=True)
        if self.delete_folders != "":
            self.rename(add="_DEL", to_find=self.delete_folders, verbose=True)

    def handle_clean(self):
        """
        Description:
            Handle clean class options.
        """
        if self.option == "show_removable":
            self.show_removable()
        if self.option == "show_nocopy":
            self.show_nocopy()
        if self.option == "full_clean":
            self.full_clean()
        if self.option == "rename":
            self.rename(to_find=self.nocopy, add="_NC", verbose=True)
            if self.delete_folders != "":
                self.rename(add="_DEL", to_find=self.delete_folders, verbose=True)
        if self.option == "clean":
            self.delete()
        if self.option == "revert_renaming":
            self.revert_renaming()
