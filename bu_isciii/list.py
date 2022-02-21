#!/usr/bin/env python

from rich.console import Console
from rich.table import Table

# Funcion

def list_pipelines ():
    """
    Print out a list of all pipelines of BU-ISCIII
    """
    return

def load_json():
    """
    Load pipelines json
    """
    return


# Print the table

table = Table(title="BU-ISCIII Tools")
table.add_column("Pipeline name", justify="right", style="cyan", no_wrap=True)
table.add_column("Latest Release", style="magenta")
table.add_column("Released", justify="right", style="green")
table.add_column("Last Pulled", justify="right", style="green")

table.add_row("viralrecon", "2.3.1", "Two weeks ago", "4 months ago")

console = Console()
console.print(table)

