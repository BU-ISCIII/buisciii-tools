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
    def __init__(self):
        # Lists available bu-isciii services and versions.
        with open(
            "/home/alberto.lema/Documents/Desarrollo/buisciii-tools/templates/services.json",
            "r",
        ) as f:
            data = json.load(f)
        pass


def list_filter():
    """Filter available bu-isciii services"""
    pass


def list_sort():
    """Sort available bu-isciii services"""
    pass


# get path real
with open(
    "/home/alberto.lema/Documents/Desarrollo/buisciii-tools/templates/services.json",
    "r",
) as f:
    data = json.load(f)

# printing elements dict

table = rich.table.Table()
table.add_column("Service name", justify="right", style="cyan")
table.add_column("Description", justify="left", style="green")

for i in data.keys():

    table.add_row(str(i), str(data[i]["description"]))
    table.add_row(str(i), str(data[i]["description"]))

console = rich.console.Console()
console.print(table)
