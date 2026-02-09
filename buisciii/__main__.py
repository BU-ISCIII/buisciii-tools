#!/usr/bin/env python


import logging
import os
from datetime import datetime
import sys
import tempfile

import click
import rich.console
import rich.logging
import rich.traceback

import buisciii
import buisciii.config_json
import buisciii.utils
import buisciii.new_service
import buisciii.scratch
import buisciii.list
import buisciii.bioinfo_doc
import buisciii.clean
import buisciii.archive
import buisciii.copy_sftp
import buisciii.autoclean_sftp

log = logging.getLogger()

# Set up rich stderr console
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


def run_buisciii():
    # Set up rich stderr console
    stderr = rich.console.Console(
        stderr=True, force_terminal=buisciii.utils.rich_force_colors()
    )

    # Set up the rich traceback
    rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)

    # Print nf-core header
    stderr.print(
        r"[blue]                 ___              ___    ___   ___  ___   ___   ____   ",
        highlight=False,
    )
    stderr.print(
        r"[blue]   \    |-[grey39]-|  [blue]  |   \   |   |      |    |     |      |     |      |    ",
        highlight=False,
    )
    stderr.print(
        r"[blue]    \   \  [grey39]/ [blue]   |__ /   |   | ___  |    |__   |      |     |      |    ",
        highlight=False,
    )
    stderr.print(
        r"[blue]    /  [grey39] / [blue] \    |   \   |   |      |       |  |      |     |      |    ",
        highlight=False,
    )
    stderr.print(
        r"[blue]   /   [grey39] |-[blue]-|    |__ /   |___|     _|__  ___|  |___  _|_   _|_    _|_   ",
        highlight=False,
    )

    __version__ = "2.3.0"
    stderr.print(
        "[grey39]    BUISCIII-tools version {}".format(__version__), highlight=False
    )

    # Launch the click cli
    buisciii_cli()


# Customise the order of subcommands for --help
class CustomHelpOrder(click.Group):
    def __init__(self, *args, **kwargs):
        self.help_priorities = {}
        super(CustomHelpOrder, self).__init__(*args, **kwargs)

    def get_help(self, ctx):
        self.list_commands = self.list_commands_for_help
        return super(CustomHelpOrder, self).get_help(ctx)

    def list_commands_for_help(self, ctx):
        """reorder the list of commands when listing the help"""
        commands = super(CustomHelpOrder, self).list_commands(ctx)
        return (
            c[1]
            for c in sorted(
                (self.help_priorities.get(command, 1000), command)
                for command in commands
            )
        )

    def command(self, *args, **kwargs):
        """
        Behaves the same as `click.Group.command()` except capture
        a priority for listing command names in help.
        """
        help_priority = kwargs.pop("help_priority", 1000)
        help_priorities = self.help_priorities

        def decorator(f):
            cmd = super(CustomHelpOrder, self).command(*args, **kwargs)(f)
            help_priorities[cmd.name] = help_priority
            return cmd

        return decorator


def setup_automatic_logging(service_path, resolution_id, command_name, conf):
    """
    Description:
        Configure automatic logging for a service execution.

        This function creates and configures a log file associated with a specific
        service execution. The log file is generally stored inside the `DOC`
        directory of the service.

    Params:
        service_path : str
            Path to the root directory of the service where the log file will be
            created.
        resolution_id : str
            Unique identifier of the resolution.
        command_name : str
            Name of the module being executed.

    Returns:
        log_filepath : str or None
            Full path to the created log file if logging was successfully configured.
            Returns None if the service path does not exist, required parameters are
            missing, or an error occurs during logging setup.
    """

    try:
        # Path verification
        if command_name == "new_service" and not os.path.exists(service_path):
            stderr.print(f"[red]Service path does not exist: {service_path}!")
            sys.exit(1)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_path = conf.get_configuration("global").get("data_path")

        if command_name == "archive":
            archive_logs_dir = f"{data_path}/logs/archive/{datetime.now().year}"
            if not os.path.exists(archive_logs_dir):
                try:
                    os.makedirs(archive_logs_dir, exist_ok=True)
                except Exception as e:
                    print(f"Could not create archive directory: {e}")
                    archive_logs_dir = tempfile.gettempdir()
            log_filename = f"{command_name}_{timestamp}.log"
            log_filepath = os.path.join(archive_logs_dir, log_filename)

        elif command_name == "autoclean-sftp" and service_path is None:
            logs_base_dir = f"{data_path}/logs"
            service_path = os.path.join(
                logs_base_dir, command_name, str(datetime.now().year)
            )
            if not os.path.exists(service_path):
                try:
                    os.makedirs(service_path, exist_ok=True)
                except Exception as e:
                    print(f"Could not create autoclean-sftp directory: {e}")
                    service_path = tempfile.gettempdir()
            log_filename = f"{command_name}_{timestamp}.log"
            log_filepath = os.path.join(service_path, log_filename)

        else:
            if command_name == "bioinfo-doc":
                doc_path = service_path
            else:
                doc_path = os.path.join(service_path, "DOC")

            # If DOC does not exist, it is created
            if not os.path.exists(doc_path) and command_name != "archive":
                try:
                    os.makedirs(doc_path, exist_ok=True)
                except Exception as e:
                    print(f"Could not create DOC directory: {e}")
                    # If this is not posible, the service folder is used
                    doc_path = service_path

            log_filename = f"{resolution_id}_{command_name}_{timestamp}.log"
            log_filepath = os.path.join(doc_path, log_filename)

        log_fh = logging.FileHandler(log_filepath, encoding="utf-8")
        log_fh.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(name)-20s [%(levelname)-7s]  %(message)s"
            )
        )

        log.addHandler(log_fh)

        print(f"Log will be saved to: {log_filepath}")

        return log_filepath

    except Exception as e:
        print(f"Error setting up automatic logging: {e}")
        return None


@click.group(cls=CustomHelpOrder)
@click.version_option(buisciii.__version__)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Print verbose output to the console.",
)
@click.option(
    "-l", "--log-file", help="Save a verbose log to a file.", metavar="<filename>"
)
@click.option(
    "-u",
    "--api_user",
    help="User for the API logging",
    required=False,
    default=None,
)
@click.option(
    "-p",
    "--api_password",
    help="Password for the API logging",
    required=False,
    default=None,
)
@click.option(
    "-c",
    "--cred_file",
    help="Config file with API logging credentials",
    required=False,
    default=None,
)
@click.option(
    "-D",
    "--debug",
    is_flag=True,
    default=False,
    help="Show the full traceback on error for debugging purposes.",
)
@click.option("-d", "--dev", help="Develop settings", is_flag=True, default=False)
@click.pass_context
def buisciii_cli(ctx, verbose, log_file, api_user, api_password, cred_file, dev, debug):
    if debug:
        # Set the base logger to output everything
        log.setLevel(logging.DEBUG)
    else:
        # Set the base logger to hide DEBUG messages
        log.setLevel(logging.INFO)

    ctx.obj = {}

    # If -l was specified, save log in the indicated file
    ctx.obj["manual_log_file"] = log_file

    if dev:
        conf = buisciii.config_json.ConfigJson(
            json_file=os.path.join(
                os.path.dirname(__file__), "conf", "configuration_dev.json"
            )
        )
    else:
        conf = buisciii.config_json.ConfigJson()

    ctx.obj["conf"] = conf
    ctx.obj.update(buisciii.utils.get_yaml_config(conf, cred_file))
    ctx.obj["debug"] = debug

    # Manual logging if -l was specified
    if log_file:
        try:
            log_fh = logging.FileHandler(log_file, encoding="utf-8")
            log_fh.setFormatter(
                logging.Formatter(
                    "[%(asctime)s] %(name)-20s [%(levelname)-7s]  %(message)s"
                )
            )
            log.addHandler(log_fh)
            print(f"Manual log will be saved to: {log_file}")
        except Exception as e:
            print(f"Warning: Could not setup manual logging: {e}")

    if buisciii.utils.validate_api_credentials(ctx.obj):
        print("API credentials successfully extracted from yaml config file")
    else:
        if api_user:
            ctx.obj["api_user"] = api_user
        else:
            ctx.obj["api_user"] = buisciii.utils.ask_for_some_text("API user: ")
        if api_password:
            ctx.obj["api_password"] = api_password
        else:
            ctx.obj["api_password"] = buisciii.utils.ask_password("API password: ")


# SERVICE LIST
@buisciii_cli.command(help_priority=1)
@click.argument("service", required=False, default=None, metavar="<service>")
@click.pass_context
def list(ctx, service):
    """
    List all available buisciii services.
    """
    service_list = buisciii.list.ListServices()
    service_list.print_table(service)


# CREATE NEW SERVICE
@buisciii_cli.command(help_priority=2)
@click.argument("resolution", required=False, default=None, metavar="<resolution id>")
@click.option(
    "-p",
    "--path",
    type=click.Path(),
    default=None,
    help="Path to create the service folder",
)
@click.option(
    "-n",
    "--no_create_folder",
    is_flag=True,
    default=None,
    help="No create service folder, only resolution",
)
@click.option(
    "-a",
    "--ask_path",
    is_flag=True,
    default=False,
    help="Please ask for path.",
)
@click.pass_context
def new_service(ctx, resolution, path, no_create_folder, ask_path):
    """
    Create new service: this will create the service folder and copy templates depending on selected service/s.
    """
    if resolution is None:
        resolution = buisciii.utils.prompt_resolution_id()

    debug = ctx.obj.get("debug", False)
    try:
        new_ser = buisciii.new_service.NewService(
            resolution,
            path,
            no_create_folder,
            ask_path,
            ctx.obj["api_user"],
            ctx.obj["api_password"],
            ctx.obj["conf"],
            setup_logging_cb=(
                None
                if ctx.obj.get("manual_log_file")
                else lambda service_path: setup_automatic_logging(
                    service_path, resolution, "new_service", ctx.obj["conf"]
                )
            ),
        )

        new_ser.create_new_service()

    except Exception as e:
        if debug:
            log.exception(f"EXCEPTION FOUND: {e}")
            raise
        else:
            log.exception(f"EXCEPTION FOUND: {e}")
            stderr.print(f"EXCEPTION FOUND: {e}")
            sys.exit(1)


# COPY SERVICE FOLDER TO SCRATCHS TMP
@buisciii_cli.command(help_priority=3)
@click.argument("resolution", required=False, default=None, metavar="<resolution id>")
@click.option(
    "-p",
    "--path",
    type=click.Path(),
    default=None,
    help="Absolute path to the folder containing service to copy",
)
@click.option(
    "-a",
    "--ask_path",
    is_flag=True,
    default=False,
    help="Please ask for service path.",
)
@click.option(
    "-t",
    "--tmp_dir",
    type=click.Path(),
    default="/scratch/bi/",
    help="Directory to which the files will be transfered for execution. Default: /data/ucct/bi/scratch_tmp/bi/",
)
@click.option(
    "-d",
    "--direction",
    type=click.Choice(["service_to_scratch", "scratch_to_service", "remove_scratch"]),
    multiple=False,
    help=(
        "Direction of the rsync command. service_to_scratch "
        "from /data/ucct/bi/service to /data/ucct/bi/scratch_tmp/bi/."
        "scratch_to_service: From /data/ucct/bi/scratch_tmp/bi/ to /data/ucct/bi/service"
    ),
)
@click.pass_context
def scratch(ctx, resolution, path, tmp_dir, direction, ask_path):
    """
    Copy service folder to scratch directory for execution.
    """
    if resolution is None:
        resolution = buisciii.utils.prompt_resolution_id()

    debug = ctx.obj.get("debug", False)
    try:
        scratch_copy = buisciii.scratch.Scratch(
            resolution,
            path,
            tmp_dir,
            direction,
            ask_path,
            ctx.obj["api_user"],
            ctx.obj["api_password"],
            ctx.obj["conf"],
        )

        # Automatic logging
        if resolution and not ctx.obj.get("manual_log_file"):
            setup_automatic_logging(
                scratch_copy.full_path, resolution, "scratch", ctx.obj["conf"]
            )

        scratch_copy.handle_scratch()
    except Exception as e:
        if debug:
            log.exception(f"EXCEPTION FOUND: {e}")
            raise
        else:
            log.exception(f"EXCEPTION FOUND: {e}")
            stderr.print(f"EXCEPTION FOUND: {e}")
            sys.exit(1)


# CLEAN SERVICE
@buisciii_cli.command(help_priority=2)
@click.argument("resolution", required=False, default=None, metavar="<resolution id>")
@click.option(
    "-p",
    "--path",
    type=click.Path(),
    default=None,
    help="Absolute path to the folder containing service to clean",
)
@click.option(
    "-a",
    "--ask_path",
    is_flag=True,
    default=False,
    help="Please ask for path",
)
@click.option(
    "-s",
    "--option",
    type=click.Choice(
        [
            "full_clean",
            "rename",
            "clean",
            "revert_renaming",
            "show_removable",
            "show_nocopy",
        ]
    ),
    multiple=False,
    help=(
        "Select what to do inside the cleanning step: full_clean: delete files and folders to clean,"
        " rename no copy and deleted folders, rename: just rename folders, clean: "
        "delete files and folders to clean,"
        "revert_renaming: remove no_copy and delete tags,"
        "show_removable: list folders and files to remove "
        "and show_nocopy: show folders to rename with no_copy tag."
    ),
)
@click.pass_context
def clean(ctx, resolution, path, ask_path, option):
    """
    Service cleaning. This will either remove big files, rename folders before copy, revert this renaming,
    show removable files or show folders for no copy.
    """
    if resolution is None:
        resolution = buisciii.utils.prompt_resolution_id()

    debug = ctx.obj.get("debug", False)
    try:
        clean_obj = buisciii.clean.CleanUp(
            resolution,
            path,
            ask_path,
            option,
            ctx.obj["api_user"],
            ctx.obj["api_password"],
            ctx.obj["conf"],
        )

        # Automatic logging
        if resolution and not ctx.obj.get("manual_log_file"):
            setup_automatic_logging(
                clean_obj.full_path, resolution, "clean", ctx.obj["conf"]
            )

        clean_obj.handle_clean()
    except Exception as e:
        if debug:
            log.exception(f"EXCEPTION FOUND: {e}")
            raise
        else:
            log.exception(f"EXCEPTION FOUND: {e}")
            stderr.print(f"EXCEPTION FOUND: {e}")
            sys.exit(1)


# COPY RESULTS FOLDER TO SFTP
@buisciii_cli.command(help_priority=4)
@click.argument("resolution", required=False, default=None, metavar="<resolution id>")
@click.option(
    "-p",
    "--path",
    type=click.Path(),
    default=None,
    help="Absolute path to directory containing files to transfer",
)
@click.option(
    "-a",
    "--ask_path",
    is_flag=True,
    default=False,
    help="Please ask for path",
)
@click.option(
    "-s",
    "--sftp_folder",
    type=click.Path(),
    default=None,
    help="Absolute path to directory to which the files will be transfered",
)
@click.pass_context
def copy_sftp(ctx, resolution, path, ask_path, sftp_folder):
    """
    Copy resolution folder to SFTP, change status of the resolution in iSkyLIMS and generate md, pdf & html files.
    """
    if resolution is None:
        resolution = buisciii.utils.prompt_resolution_id()

    debug = ctx.obj.get("debug", False)
    try:
        new_del = buisciii.copy_sftp.CopySftp(
            resolution,
            path,
            ask_path,
            sftp_folder,
            ctx.obj["api_user"],
            ctx.obj["api_password"],
            ctx.obj["conf"],
        )

        # Automatic logging
        if resolution and not ctx.obj.get("manual_log_file"):
            setup_automatic_logging(
                new_del.full_path, resolution, "copy_sftp", ctx.obj["conf"]
            )

        new_del.copy_sftp()
    except Exception as e:
        if debug:
            log.exception(f"EXCEPTION FOUND: {e}")
            raise
        else:
            log.exception(f"EXCEPTION FOUND: {e}")
            stderr.print(f"EXCEPTION FOUND: {e}")
            sys.exit(1)


# CLEAN SCRATCH, COPY TO SERVICE, RENAME SERVICE AND COPY RESULTS FOLDER TO SFTP
@buisciii_cli.command(help_priority=5)
@click.argument("resolution", required=False, default=None, metavar="<resolution id>")
@click.option(
    "-p",
    "--path",
    type=click.Path(),
    default=None,
    help="Absolute path to the folder containg the service to reaname and copy",
)
@click.option(
    "-a",
    "--ask_path",
    is_flag=True,
    default=False,
    help="Please ask for path, not assume pwd.",
)
@click.option(
    "-s",
    "--sftp_folder",
    type=click.Path(),
    default=None,
    help="Absolute path to directory to which the files will be transfered",
)
@click.option(
    "-t",
    "--tmp_dir",
    type=click.Path(),
    default="/scratch/bi/",
    help="Absolute path to the scratch directory containing the service.",
)
@click.pass_context
def finish(ctx, resolution, path, ask_path, sftp_folder, tmp_dir):
    """
    Service cleaning, big files removal, folders renaming before copy and resolution folder copying to the SFTP.
    """
    if resolution is None:
        resolution = buisciii.utils.prompt_resolution_id()

    clean_tmp_dir = tmp_dir
    if tmp_dir == "/scratch/bi/":
        clean_tmp_dir = "/data/ucct/bi/scratch_tmp/bi"

    conf = buisciii.config_json.ConfigJson()
    conf_api = conf.get_configuration("xtutatis_api_settings")
    rest_api = buisciii.drylab_api.RestServiceApi(
        conf_api["server"],
        conf_api["api_url"],
        ctx.obj["api_user"],
        ctx.obj["api_password"],
    )
    resolution_info = rest_api.get_request(
        request_info="service-data", safe=True, resolution=resolution
    )
    service_folder = resolution_info["resolutions"][0]["resolution_full_number"]
    service_path = os.path.join(
        buisciii.utils.get_service_paths(
            conf, "services_and_colaborations", resolution_info, "non_archived_path"
        ),
        service_folder,
    )

    if not ctx.obj.get("manual_log_file"):
        setup_automatic_logging(service_path, resolution, "finish", ctx.obj["conf"])

    print("Starting cleaning scratch directory: " + clean_tmp_dir)
    clean_scratch = buisciii.clean.CleanUp(
        resolution,
        clean_tmp_dir,
        ask_path,
        "clean",
        ctx.obj["api_user"],
        ctx.obj["api_password"],
        ctx.obj["conf"],
    )
    clean_scratch.handle_clean()
    print("Starting copy from scratch directory: " + tmp_dir + " to service directory.")
    copy_scratch2service = buisciii.scratch.Scratch(
        resolution,
        path,
        tmp_dir,
        "scratch_to_service",
        ask_path,
        ctx.obj["api_user"],
        ctx.obj["api_password"],
        ctx.obj["conf"],
    )
    copy_scratch2service.handle_scratch()
    print("Starting renaming of the service directory.")
    rename_databi = buisciii.clean.CleanUp(
        resolution,
        path,
        ask_path,
        "rename",
        ctx.obj["api_user"],
        ctx.obj["api_password"],
        ctx.obj["conf"],
    )
    rename_databi.handle_clean()
    print("Starting copy of the service directory to the SFTP folder")
    copy_sftp = buisciii.copy_sftp.CopySftp(
        resolution,
        path,
        ask_path,
        sftp_folder,
        ctx.obj["api_user"],
        ctx.obj["api_password"],
        ctx.obj["conf"],
    )
    copy_sftp.copy_sftp()

    print("Service correctly stored in the SFTP folder")
    print("Remember to generate delivery docs after setting delivery in iSkyLIMS!")


# CREATE DOCS IN BIOINFO_DOC
@buisciii_cli.command(help_priority=6)
@click.argument("resolution", required=False, default=None, metavar="<resolution id>")
@click.option(
    "-p",
    "--path",
    type=click.Path(),
    default=None,
    help="Absolute path to bioinfo_doc directory.",
)
@click.option(
    "-a",
    "--ask_path",
    is_flag=True,
    default=False,
    help="Please ask for path, not assume /data/bioinfo_doc/.",
)
@click.option(
    "-t",
    "--type",
    type=click.Choice(["service_info", "delivery"]),
    help="Select the documentation that will generate",
)
@click.option(
    "-s",
    "--sftp_folder",
    type=click.Path(),
    default=None,
    help="Absolute path to sftp folfer containing service folder",
)
@click.option(
    "-r",
    "--report_md",
    type=click.Path(),
    default=None,
    help="Absolute path to markdown report to use instead of the one in config file",
)
@click.option(
    "-m",
    "--results_md",
    type=click.Path(),
    default=None,
    help="Absolute path to markdown report to use instead of the one in config file",
)
@click.option(
    "-e",
    "--email_psswd",
    help="Password for bioinformatica@isciii.es",
    required=False,
    default=None,
)
@click.pass_context
def bioinfo_doc(
    ctx,
    type,
    resolution,
    path,
    ask_path,
    sftp_folder,
    report_md,
    results_md,
    email_psswd,
):
    """
    Create the folder documentation structure in bioinfo_doc server
    """
    if resolution is None:
        resolution = buisciii.utils.prompt_resolution_id()

    debug = ctx.obj.get("debug", False)
    try:
        email_pass = email_psswd if email_psswd else ctx.obj.get("email_password")
        new_doc = buisciii.bioinfo_doc.BioinfoDoc(
            type,
            resolution,
            path,
            ask_path,
            sftp_folder,
            report_md,
            results_md,
            ctx.obj["api_user"],
            ctx.obj["api_password"],
            ctx.obj["conf"],
            email_pass,
        )

        if resolution and not ctx.obj.get("manual_log_file"):
            logs_directory = os.path.join(
                new_doc.path,
                new_doc.conf["services_path"],
                datetime.strftime(new_doc.resolution_datetime, "%Y"),
                "logs",
            )
            setup_automatic_logging(
                logs_directory, resolution, "bioinfo-doc", ctx.obj["conf"]
            )

        new_doc.create_documentation()

    except Exception as e:
        if debug:
            log.exception(f"EXCEPTION FOUND: {e}")
            raise
        else:
            log.exception(f"EXCEPTION FOUND: {e}")
            stderr.print(f"EXCEPTION FOUND: {e}")
            sys.exit(1)


# ARCHIVE SERVICES
@buisciii_cli.command(help_priority=7)
@click.option("-s", "--service_id", default=None, help="service id, pe SRVCNM787")
@click.option(
    "-sf", "--service_file", default=None, help="file with services ids, one per line"
)
@click.option(
    "-t",
    "--ser_type",
    type=click.Choice(["services_and_colaborations", "research"]),
    help="Select which folder you want to archive.",
)
@click.option(
    "-o",
    "--option",
    type=click.Choice(["archive", "retrieve_from_archive"]),
    help="Select either you want to archive services or retrieve a service from archive.",
)
@click.option(
    "-sp",
    "--skip_prompts",
    is_flag=True,
    help="Avoid prompts (except on service choosing)",
)
@click.option(
    "-df",
    "--date_from",
    default=None,
    help="The date from which start search (format 'YYYY-MM-DD')",
)
@click.option(
    "-du",
    "--date_until",
    default=None,
    help="The date from which end search (format 'YYYY-MM-DD')",
)
@click.option(
    "-f",
    "--output_name",
    default=None,
    help="Tsv output path + filename with archive stats and info",
)
@click.pass_context
def archive(
    ctx,
    service_id,
    service_file,
    ser_type,
    option,
    skip_prompts,
    date_from,
    date_until,
    output_name,
):
    """
    Archive services or retrieve services from archive
    """

    debug = ctx.obj.get("debug", False)
    try:
        # Automatic logging
        if not ctx.obj.get("manual_log_file"):
            setup_automatic_logging(None, None, "archive", ctx.obj["conf"])

        archive_ser = buisciii.archive.Archive(
            service_id,
            service_file,
            ser_type,
            option,
            ctx.obj["api_user"],
            ctx.obj["api_password"],
            ctx.obj["conf"],
            skip_prompts,
            date_from,
            date_until,
            output_name,
        )

        archive_ser.handle_archive()

    except Exception as e:
        if debug:
            log.exception(f"EXCEPTION FOUND: {e}")
            raise
        else:
            log.exception(f"EXCEPTION FOUND: {e}")
            stderr.print(f"EXCEPTION FOUND: {e}")
            sys.exit(1)


# CLEAN OLD SFTP SERVICES
@buisciii_cli.command(help_priority=8)
@click.option(
    "-s",
    "--sftp_folder",
    type=click.Path(),
    default=None,
    help="Absolute path to sftp folder",
)
@click.option(
    "-d",
    "--days",
    type=int,
    default=14,
    help="Integer, remove files older than a window of `-d [int]` days. Default 14 days.",
)
@click.pass_context
def autoclean_sftp(ctx, sftp_folder, days):
    """Clean old sftp services"""

    debug = ctx.obj.get("debug", False)
    try:
        sftp_clean = buisciii.autoclean_sftp.AutoremoveSftpService(
            sftp_folder, days, ctx.obj["conf"]
        )

        # Automatic logging
        if not ctx.obj.get("manual_log_file"):
            setup_automatic_logging(None, None, "autoclean-sftp", ctx.obj["conf"])

        sftp_clean.handle_autoclean_sftp()

    except Exception as e:
        if debug:
            log.exception(f"EXCEPTION FOUND: {e}")
            raise
        else:
            log.exception(f"EXCEPTION FOUND: {e}")
            stderr.print(f"EXCEPTION FOUND: {e}")
            sys.exit(1)


# FIX PERMISSIONS
@buisciii_cli.command(help_priority=9)
@click.option(
    "-d",
    "--input_directory",
    type=click.Path(),
    multiple=True,
    default=None,
    required=True,
    help="Input directory to fix permissions (absolute path)",
)
@click.pass_context
def fix_permissions(ctx, input_directory):
    """
    Fix permissions
    """
    debug = ctx.obj.get("debug", False)
    conf = buisciii.config_json.ConfigJson()
    permissions = conf.get_configuration("global").get("permissions")
    stderr = rich.console.Console(
        stderr=True, force_terminal=buisciii.utils.rich_force_colors()
    )

    for directory in input_directory:
        if not os.path.isdir(directory):
            stderr.print(f"[red]Invalid input directory: {directory}")
            continue
        try:
            buisciii.utils.remake_permissions(directory, permissions)
            stderr.print(f"[green]Correct permissions were applied to {directory}")
        except Exception as e:
            if debug:
                log.exception(f"EXCEPTION FOUND: {e}")
                raise
            else:
                log.exception(f"EXCEPTION FOUND: {e}")
                stderr.print(f"EXCEPTION FOUND: {e}")
                sys.exit(1)


if __name__ == "__main__":
    run_buisciii()
