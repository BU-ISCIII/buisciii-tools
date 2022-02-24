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
from bu_isciii.service_json import ServiceJson


class ListServices:
    def __init__(self, json_file):
        data_json = ServiceJson.get_json_data(json_file)

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
        """
        Colaboración de Pablo
        """
        if found in self.json_data[service]:
            return self.json_data[service][found]
        else:
            for key, value in self.json_data[service].items():
                if isinstance(value, dict):
                    if found in self.json_data[service][key]:
                        return self.json_data[service][key]
            return None


prueba = ListServices("templates/services.json")
prueba()

print(prueba.json_data)

prueba = ListServices("templates/services.json")
prueba.get_find("assembly_annotation", "clean")
