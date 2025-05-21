#!/usr/bin/env python

# import sys
import logging
import os

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


def run_buisciii():
    # Set up rich stderr console
    stderr = rich.console.Console(
        stderr=True, force_terminal=buisciii.utils.rich_force_colors()
    )

    # Set up the rich traceback
    rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)

    # Print nf-core header
    # stderr.print("\n[green]{},--.[grey39]/[green],-.".format(" " * 42), highlight=False)
    stderr.print(
        "[blue]                 ___              ___    ___   ___  ___   ___   ____   ",
        highlight=False,
    )
    stderr.print(
        "[blue]   \    |-[grey39]-|  [blue]  |   \   |   |      |    |     |      |     |      |    ",
        highlight=False,
    )
    stderr.print(
        "[blue]    \   \  [grey39]/ [blue]   |__ /   |   | ___  |    |__   |      |     |      |    ",
        highlight=False,
    )
    stderr.print(
        "[blue]    /  [grey39] / [blue] \    |   \   |   |      |       |  |      |     |      |    ",
        highlight=False,
    )
    stderr.print(
        "[blue]   /   [grey39] |-[blue]-|    |__ /   |___|     _|__  ___|  |___  _|_   _|_    _|_   ",
        highlight=False,
    )

    # stderr.print("[green]                                          `._,._,'\n", highlight=False)
    __version__ = "2.2.10"
    stderr.print(
        "[grey39]    BU-ISCIII-tools version {}".format(__version__), highlight=False
    )

    # Lanch the click cli
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
        """Behaves the same as `click.Group.command()` except capture
        a priority for listing command names in help.
        """
        help_priority = kwargs.pop("help_priority", 1000)
        help_priorities = self.help_priorities

        def decorator(f):
            cmd = super(CustomHelpOrder, self).command(*args, **kwargs)(f)
            help_priorities[cmd.name] = help_priority
            return cmd

        return decorator


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
@click.option("-d", "--dev", help="Develop settings", is_flag=True, default=False)
@click.pass_context
def buisciii_cli(ctx, verbose, log_file, api_user, api_password, cred_file, dev):
    # Set the base logger to output DEBUG
    log.setLevel(logging.INFO)
    # Initialize context
    ctx.obj = {}
    # Set up logs to a file if we asked for one
    if log_file:
        log_fh = logging.FileHandler(log_file, encoding="utf-8")
        log_fh.setLevel(logging.INFO)
        log_fh.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(name)-20s [%(levelname)-7s]  %(message)s"
            )
        )
        log.addHandler(log_fh)

    if dev:
        conf = buisciii.config_json.ConfigJson(
            json_file=os.path.join(
                os.path.dirname(__file__), "conf", "configuration_dev.json"
            )
        )
    else:
        conf = buisciii.config_json.ConfigJson()

    ctx.obj = buisciii.utils.get_yaml_config(conf, cred_file)
    ctx.obj["conf"] = conf

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
    List available bu-isciii services.
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
    Create new service, it will create folder and copy template depending on selected service.
    """
    new_ser = buisciii.new_service.NewService(
        resolution,
        path,
        no_create_folder,
        ask_path,
        ctx.obj["api_user"],
        ctx.obj["api_password"],
        ctx.obj["conf"],
    )
    new_ser.create_new_service()


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
    default="/data/ucct/bi/scratch_tmp/bi/",
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
    scratch_copy.handle_scratch()


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
    Service cleaning. It will either remove big files, rename folders before copy, revert this renaming,
    show removable files or show folders for no copy.
    """
    clean = buisciii.clean.CleanUp(
        resolution,
        path,
        ask_path,
        option,
        ctx.obj["api_user"],
        ctx.obj["api_password"],
        ctx.obj["conf"],
    )
    clean.handle_clean()


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
    Copy resolution FOLDER to sftp, change status of resolution in iskylims and generate md, pdf, html.
    """
    new_del = buisciii.copy_sftp.CopySftp(
        resolution,
        path,
        ask_path,
        sftp_folder,
        ctx.obj["api_user"],
        ctx.obj["api_password"],
        ctx.obj["conf"],
    )
    new_del.copy_sftp()


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
    default="/data/ucct/bi/scratch_tmp/bi/",
    help="Absolute path to the scratch directory containing the service.",
)
@click.pass_context
def finish(ctx, resolution, path, ask_path, sftp_folder, tmp_dir):
    """
    Service cleaning, remove big files, rename folders before copy and copy resolution FOLDER to sftp.
    """
    print("Starting cleaning scratch directory: " + tmp_dir)
    clean_scratch = buisciii.clean.CleanUp(
        resolution,
        tmp_dir,
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
    print("Service correctly in SFTP folder")
    print("Remember to generate delivery docs after setting delivery in iSkyLIMS.")


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
    new_doc.create_documentation()


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
    sftp_clean = buisciii.autoclean_sftp.AutoremoveSftpService(
        sftp_folder, days, ctx.obj["conf"]
    )
    sftp_clean.handle_autoclean_sftp()


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
    conf = buisciii.config_json.ConfigJson()
    permissions = conf.get_configuration("global").get("permissions")
    stderr = rich.console.Console(
        stderr=True, force_terminal=buisciii.utils.rich_force_colors()
    )

    for directory in input_directory:
        if not os.path.isdir(directory):
            stderr.print(f"[red]Invalid input directory: {directory}")
            continue
        buisciii.utils.remake_permissions(directory, permissions)
        stderr.print(f"[green]Correct permissions were applied to {directory}")


if __name__ == "__main__":
    run_buisciii()
