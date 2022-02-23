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

    def get_find(self, service, found):
        if found in self.json_data[service]:
            return self.json_data[service][found]
        else:
            for key, value in self.data[service].items():
                if isinstance(value, dict):
                    if found in self.data[service][key]:
                        return self.data[service][key]
            return None


prueba = ListServices("../templates/services.json")
prueba.get_find("assembly_annotation", "clean")
