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
    def __init__(self):
        service_json = ServiceJson()
        service_data = service_json.get_json_data()
        print(service_data)

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


prueba = ListServices()
prueba = ServiceJson()


prueba.get_find("assembly_annotation", "clean")
