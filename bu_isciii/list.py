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

from importlib.resources import path
import json
from ossaudiodev import openmixer
import rich.table
import rich.console
import os

class list_services ():
    """Lists available bu-isciii services and versions.
    """
    pass

def read_json():
    """Read available bu-isciii services in json.
    """
    pass

def list_filter():
    """Filter available bu-isciii services
    """
    pass

def list_sort():
    """Sort available bu-isciii services
    """
    pass

# get path real
with open('/home/alberto.lema/Documents/Desarrollo/buisciii-tools/templates/services.json', 'r') as f:
  data = json.load(f)

# printing elements dict

table = rich.table.Table()
table.add_column("Service name", justify="right", style="cyan")

print (data["assembly_annotation"]["description"])

for i in data.keys():
    table.add_row(str(i))

console = rich.console.Console()
console.print(table)
