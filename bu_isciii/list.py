#!/usr/bin/env python

import json
import rich.table
import rich.console

def print_table():
    """Lists available bu-isciii pipelines and versions.
    """
    pass

def list_pipelines():
    """Prints out a list of all bu-isciii pipelines.
    """
    pass

table = rich.table.Table()
table.add_column("Service name", justify="right", style="cyan"),
table.add_column("Version", justify="right", style="green")

table.add_row("viralrecon", "v2.1.0")

console = rich.console.Console()
console.print(table)



