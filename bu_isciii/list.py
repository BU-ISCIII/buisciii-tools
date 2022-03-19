#!/usr/bin/env python

"""
 =============================================================
 HEADER
 =============================================================
 INSTITUTION: BU-ISCIII
 AUTHOR: Alberto Lema Blanco
 ================================================================
 END_OF_HEADER
 ================================================================
"""

import rich.table
import rich.console
from bu_isciii.service_json import ServiceJson
import re


class ListServices:
    def __init__(self):
        service_json = ServiceJson()
        self.service_data = service_json.get_json_data()
        self.service_list = service_json.get_service_list()

    def print_table(self, service=None):
        """
        Table print for services names and description
        """

        if service:
            search = re.compile(service)
            subset_services = list(filter(search.match, self.service_list))
        else:
            subset_services = self.service_list

        table = rich.table.Table()
        table.add_column("Service name", justify="right", style="cyan")
        table.add_column("Description", justify="left", style="green")
        table.add_column("Github", justify="left", style="green")

        for i in subset_services:
            table.add_row(
                str(i),
                str(self.service_data[i]["description"]),
                str(self.service_data[i]["url"]),
            )

        console = rich.console.Console()
        console.print(table)
