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

import json
import rich.table
import rich.console


class ListServices:
    def __init__(self, json_file):
        fh = open(json_file)
        self.json_data = json.load(fh)
        fh.close()
        self.service_list = list(self.json_data.keys())

    def get_service_list(self):
        return self.service_list

    def get_service_configuration(self, service):
        if service in self.service_list:
            return self.json_data[service]
        return None

    def get_table(self):

        # Creacion de la tabla
        table = rich.table.Table()
        table.add_column("Service name", justify="right", style="cyan")
        table.add_column("Description", justify="left", style="green")
        datos = self.json_data
        servicios = self.service_list
        for i in servicios:
            table.add_row(str(i), str(datos[i]["description"]))

        console = rich.console.Console()
        console.print(table)


"""
# get path real
with open(
    "/home/alberto.lema/Documents/Desarrollo/buisciii-tools/templates/services.json",
    "r",
) as f:
    data = json.load(f)

print(data)
servicios = list(data.keys())
servicios_files = data[servicios[1]]["clean"]
print(servicios_files)

# printing elements dict

table = rich.table.Table()
table.add_column("Service name", justify="right", style="cyan")
table.add_column("Description", justify="left", style="green")

for i in data.keys():

    table.add_row(str(i), str(data[i]["description"]))

console = rich.console.Console()
console.print(table)
"""
