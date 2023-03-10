#!/usr/bin/env python

# import sys
import logging

import click
import rich.console
import rich.logging
import rich.traceback

import bu_isciii
import bu_isciii.utils
import bu_isciii.new_service
import bu_isciii.scratch
import bu_isciii.list
import bu_isciii.bioinfo_doc
import bu_isciii.clean
import bu_isciii.archive
import bu_isciii.copy_sftp

log = logging.getLogger()


def run_bu_isciii():
    # Set up rich stderr console
    stderr = rich.console.Console(
        stderr=True, force_terminal=bu_isciii.utils.rich_force_colors()
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
    __version__ = "1.0.0"
    stderr.print(
        "[grey39]    BU-ISCIII-tools version {}".format(__version__), highlight=False
    )

    # Lanch the click cli
    bu_isciii_cli()


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
@click.version_option(bu_isciii.__version__)
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
    "-t",
    "--api-token",
    help="Password for the API logging",
    required=False,
    default=None,
)
def bu_isciii_cli(verbose, log_file, api_token):
    # Set the base logger to output DEBUG
    log.setLevel(logging.DEBUG)

    # Set up logs to a file if we asked for one
    if log_file:
        log_fh = logging.FileHandler(log_file, encoding="utf-8")
        log_fh.setLevel(logging.DEBUG)
        log_fh.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(name)-20s [%(levelname)-7s]  %(message)s"
            )
        )
        log.addHandler(log_fh)

    global api_pass
    if api_token:
        api_pass = api_token
    else:
        stderr.print("Write API password for logging")
        api_pass = bu_isciii.utils.ask_password("API password: ")


# SERVICE LIST
@bu_isciii_cli.command(help_priority=1)
@click.argument("service", required=False, default=None, metavar="<service>")
def list(service):
    """
    List available bu-isciii services.
    """
    service_list = bu_isciii.list.ListServices()
    service_list.print_table(service)


# CREATE NEW SERVICE
@bu_isciii_cli.command(help_priority=2)
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
def new_service(resolution, path, no_create_folder, ask_path):
    """
    Create new service, it will create folder and copy template depending on selected service.
    """
    new_ser = bu_isciii.new_service.NewService(
        resolution, path, no_create_folder, ask_path, api_pass
    )
    new_ser.create_new_service()


# COPY SERVICE FOLDER TO SCRATCHS TMP
@bu_isciii_cli.command(help_priority=3)
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
    default="/data/bi/scratch_tmp/bi/",
    help="Directory to which the files will be transfered for execution. Default: /data/bi/scratch_tmp/bi/",
)
@click.option(
    "-d",
    "--direction",
    type=click.Choice(["Service_to_scratch", "Scratch_to_service", "Remove_scratch"]),
    multiple=False,
    help="Direction of the rsync command. Service_to_scratch from /data/bi/service to /data/bi/scratch_tmp/bi/. Scratch_to_service: From /data/bi/scratch_tmp/bi/ to /data/bi/service",
)
def scratch(resolution, path, tmp_dir, direction, ask_path):
    """
    Copy service folder to scratch directory for execution.
    """
    scratch_copy = bu_isciii.scratch.Scratch(
        resolution, path, tmp_dir, direction, ask_path, api_pass
    )
    scratch_copy.handle_scratch()


# CLEAN SERVICE
@bu_isciii_cli.command(help_priority=2)
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
            "rename_nocopy",
            "clean",
            "revert_renaming",
            "show_removable",
            "show_nocopy",
        ]
    ),
    multiple=False,
    help="Select what to do inside the cleanning step: full_clean: delete files and folders to clean, rename no copy and deleted folders, rename_nocopy: just rename no copy folders, clean: delete files and folders to clean, revert_renaming: remove no_copy and delete tags, show_removable: list folders and files to remove and show_nocopy: show folders to rename with no_copy tag.",
)
def clean(resolution, path, ask_path, option):
    """
    Service cleaning. It will either remove big files, rename folders before copy, revert this renaming, show removable files or show folders for no copy.
    """
    clean = bu_isciii.clean.CleanUp(resolution, path, ask_path, option, api_pass)
    clean.handle_clean()


# COPY RESULTS FOLDER TO SFTP
@bu_isciii_cli.command(help_priority=4)
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
def copy_sftp(resolution, path, ask_path, sftp_folder):
    """
    Copy resolution FOLDER to sftp, change status of resolution in iskylims and generate md, pdf, html.
    """
    new_del = bu_isciii.copy_sftp.CopySftp(
        resolution, path, ask_path, sftp_folder, api_pass
    )
    new_del.copy_sftp()


# CLEAN SCRATCH, COPY TO SERVICE, RENAME SERVICE AND COPY RESULTS FOLDER TO SFTP
@bu_isciii_cli.command(help_priority=5)
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
    default="/data/bi/scratch_tmp/bi/",
    help="Absolute path to the scratch directory containing the service.",
)
def finish(resolution, path, ask_path, sftp_folder, tmp_dir):
    """
    Service cleaning, remove big files, rename folders before copy and copy resolution FOLDER to sftp.
    """
    print("Starting cleaning scratch directory: " + tmp_dir)
    clean_scratch = bu_isciii.clean.CleanUp(
        resolution, tmp_dir, ask_path, "clean", api_pass
    )
    clean_scratch.handle_clean()
    print("Starting copy from scratch directory: " + tmp_dir + " to service directory.")
    copy_scratch2service = bu_isciii.scratch.Scratch(
        resolution, path, tmp_dir, "Scratch_to_service", ask_path, api_pass
    )
    copy_scratch2service.handle_scratch()
    print("Starting renaming of the service directory.")
    rename_databi = bu_isciii.clean.CleanUp(
        resolution, path, ask_path, "rename_nocopy", api_pass
    )
    rename_databi.handle_clean()
    print("Starting copy of the service directory to the SFTP folder")
    copy_sftp = bu_isciii.copy_sftp.CopySftp(
        resolution, path, ask_path, sftp_folder, api_pass
    )
    copy_sftp.copy_sftp()
    print("Service correctly in SFTP folder")
    print("Remember to generate delivery docs after setting delivery in iSkyLIMS.")


# CREATE DOCS IN BIOINFO_DOC
@bu_isciii_cli.command(help_priority=6)
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

def bioinfo_doc(type, resolution, path, ask_path, sftp_folder, report_md, results_md, email_psswd):
    """
    Create the folder documentation structure in bioinfo_doc server
    """
    new_doc = bu_isciii.bioinfo_doc.BioinfoDoc(
        type, resolution, path, ask_path, sftp_folder, report_md, results_md, api_pass, email_psswd
    )
    new_doc.create_documentation()


# ARCHIVE SERVICES
@bu_isciii_cli.command(help_priority=7)
@click.argument("resolution", required=False, default=None, metavar="<resolution id>")
@click.option(
    "-t",
    "--type",
    type=click.Choice(["services_and_colaborations", "research"]),
    help="Select which folder you want to archive.",
)
@click.option(
    "-s",
    "--option",
    type=click.Choice(["archive", "retrieve_from_archive"]),
    help="Select either you want to archive services or retrieve a service from archive.",
)
def archive(resolution, type, option):
    """
    Archive services or retrieve services from archive
    """
    archive_ser = bu_isciii.archive.Archive(resolution, type, option, api_pass)
    archive_ser.handle_archive()


if __name__ == "__main__":
    run_bu_isciii()
