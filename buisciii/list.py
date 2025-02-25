#!/usr/bin/env python

# Generic imports
import re
import logging
import rich.table
import rich.console
from rich.console import Console

# Local imports
import buisciii
import buisciii.utils
from buisciii.service_json import ServiceJson

log = logging.getLogger(__name__)
stderr = Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


def generate_table(service_list, data_dictionary):
    """
    Given a list of services,
    generate a rich table with it
    """

    table = rich.table.Table()
    table.add_column("Service name", justify="right", style="cyan")
    table.add_column("Description", justify="left", style="green")
    table.add_column("Github", justify="left", style="green")

    for service in service_list:
        table.add_row(
            str(service),
            str(data_dictionary[service]["description"]),
            str(data_dictionary[service]["url"]),
        )

    return table


class ListServices:
    def __init__(self):
        service_json = ServiceJson()
        self.service_data = service_json.get_json_data()
        self.service_list = service_json.get_service_list()

    def print_table(self, service=None):
        """
        Print table for service
        names and description
        """

        if service:
            search = re.compile(service)
            subset_services = list(filter(search.match, self.service_list))
        else:
            subset_services = self.service_list
        if len(subset_services) == 0:
            stderr.print(f"No services with name {service} found.")
            return

        sort_dataframe = buisciii.utils.prompt_selection(
            "Would you like to print a sorted list?",
            ["Yes", "No"],
        )

        table = (
            generate_table(sorted(subset_services), self.service_data)
            if sort_dataframe == "Yes"
            else generate_table(subset_services, self.service_data)
        )

        console = rich.console.Console()
        console.print(table)
        return
