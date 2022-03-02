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
    def __init__(
        self,
    ):

        service_json = ServiceJson()
        self.service_data = service_json.get_json_data()
        self.service_list = service_json.get_service_list()

    def get_filtered(self, name):
        """
        Filter the table
        """
        r = re.compile(name)
        newlist = list(filter(r.match, self.service_list))
        print(newlist)

    def get_table(self):
        """
        Table print for services names and description
        """
        table = rich.table.Table()
        table.add_column("Service name", justify="right", style="cyan")
        table.add_column("Description", justify="left", style="green")
        table.add_column("Github", justify="left", style="green")

        for i in self.service_list:
            table.add_row(
                str(i),
                str(self.service_data[i]["description"]),
                str(self.service_data[i]["url"]),
            )

        console = rich.console.Console()
        console.print(table)


prueba = ListServices()

prueba.get_filtered("prueba")

print(prueba.service_list)
