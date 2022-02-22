#!/usr/bin/env python

import json
import rich.table
import rich.console

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



table = rich.table.Table()
table.add_column("Service name", justify="right", style="cyan"),
table.add_column("Version", justify="right", style="green")

table.add_row("viralrecon", "v2.1.0")

console = rich.console.Console()
console.print(table)



