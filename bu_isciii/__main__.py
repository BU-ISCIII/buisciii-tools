#!/usr/bin/env python

import sys
import os
import logging

import click
from click.types import File
from rich import print
from rich.prompt import Confirm
import rich.console
import rich.logging
import rich.traceback

import bu_isciii
import bu_isciii.utils
import bu_isciii.new_service

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
    __version__ = "0.0.1"
    stderr.print(
        "[grey39]    BU-ISCIII-tools version {}".format(__version__), highlight=False
    )
    try:
        pass
    except:
        pass

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
def bu_isciii_cli(verbose, log_file):

    # Set the base logger to output DEBUG
    log.setLevel(logging.DEBUG)

    # Set up logs to the console
    log.addHandler(
        rich.logging.RichHandler(
            level=logging.DEBUG if verbose else logging.INFO,
            console=rich.console.Console(
                stderr=True, force_terminal=bu_isciii.utils.rich_force_colors()
            ),
            show_time=False,
            markup=True,
        )
    )

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


# pipeline list
@bu_isciii_cli.command(help_priority=1)
@click.argument("keywords", required=False, nargs=-1, metavar="<filter keywords>")
@click.option(
    "-s",
    "--sort",
    type=click.Choice(["name", "date", "version"]),
    default="release",
    help="How to sort listed services",
)
@click.option("--json", is_flag=True, default=False, help="Print full output as JSON")
def list(keywords, sort, json, show_archived):
    """
    List available bu-isciii services.
    """
    # EXAMPLE -> print(nf_core.list.list_workflows(keywords, sort, json, show_archived))
    print("I will list available services")


@bu_isciii_cli.command(help_priority=2)
@click.argument("resolution", required=False, default=None, metavar="<resolution id>")
@click.argument("folder", required=False, default=None, metavar="<folder>")
@click.argument(
    "service_label", required=False, default=None, metavar="<service label>"
)
@click.argument("service_id", required=False, default=None, metavar="<service id>")
@click.option(
    "-p",
    "--path",
    type=click.Path(),
    default=os.getcwd(),
    help="Path to create the service folder",
)
@click.option(
    "-n",
    "--no_create_folder",
    is_flag=True,
    default=False,
    help="No create service folder, only resolution",
)
def new_service(resolution, folder, service_label, service_id, path, no_create_folder):
    """
    Create new service, it will create folder and copy template depending on selected service.
    """
    new_ser = bu_isciii.new_service.NewService(
        resolution, folder, service_label, service_id, path, no_create_folder
    )
    new_ser.create_folder()


if __name__ == "__main__":
    run_bu_isciii()
