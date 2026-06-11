#!/usr/bin/env python
"""
Specific cleaner file for viralrecon service.
This script deletes .sorted.bam files when the protocol is amplicon. If not, these files are not deleted.
"""

import sys
from pathlib import Path
import logging
from rich.console import Console

# Local imports
import buisciii
import buisciii.utils

stderr = Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)

log = logging.getLogger(__name__)


def setup_logging(service_path):
    log_file = Path(service_path) / "DOC" / "viralrecon_clean.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def get_protocol(service_path):
    """Reads protocol from config yml file"""
    doc_dir = Path(service_path) / "DOC"
    if not doc_dir.exists():
        return None

    posibles = list(doc_dir.glob("*_viralrecon_params.yml"))
    log.info(f"viralrecon_params.yml files found: {[p.name for p in posibles]}")
    if not posibles:
        posibles = list(doc_dir.glob("viralrecon_params.yml"))
        log.info(f"viralrecon_params.yml files found: {[p.name for p in posibles]}")
    if not posibles:
        return None

    params_file = posibles[0]
    log.info(f"Using params_file: {params_file}\n")
    with open(params_file) as f:
        for line in f:
            if line.startswith("protocol:"):
                protocol = line.split(":", 1)[1].strip().strip("'\"")
                stderr.print(f"Protocol defined for viralrecon = '{protocol}'")
                log.info(f"Protocol defined for viralrecon = '{protocol}'")
                return protocol
    return None


def find_bowtie2_dirs(service_path):
    """Finds all directories called 'variants/bowtie2' within the service"""
    bowtie2_dirs = []
    service_path = Path(service_path)
    stderr.print(f"Searching recursively in: {service_path}")
    log.info(f"Searching recursively in: {service_path}")
    for variants_dir in service_path.rglob("variants"):
        bowtie2_dir = variants_dir / "bowtie2"
        if bowtie2_dir.exists() and bowtie2_dir.is_dir():
            bowtie2_dirs.append(bowtie2_dir)
            stderr.print(f"Bowtie2_dir: {bowtie2_dir}")
            log.info(f"Bowtie2_dir: {bowtie2_dir}")
        else:
            stderr.print(f"Bowtie2_dir NOT FOUND: {bowtie2_dir}")
            log.info(f"Bowtie2_dir NOT FOUND: {bowtie2_dir}")
    return bowtie2_dirs


def main():
    if len(sys.argv) < 2:
        print("Usage: viralrecon_clean.py <service_path>")
        sys.exit(1)

    service_path = Path(sys.argv[1])
    setup_logging(service_path)

    service_path = Path(sys.argv[1])

    protocol = get_protocol(service_path)

    if protocol != "amplicon":
        stderr.print("The protocol is 'metagenomic', EXITING without deleting anything")
        log.info("The protocol is 'metagenomic', EXITING without deleting anything")
        return

    bowtie2_dirs = find_bowtie2_dirs(service_path)
    to_delete = []

    for bowtie2_dir in bowtie2_dirs:
        for pattern in ["*.sorted.bam", "*.sorted.bam.bai"]:
            for filepath in bowtie2_dir.glob(pattern):
                log.info(f"Evaluating file: {filepath}")
                if "ivar_trim" not in filepath.name:
                    to_delete.append(str(filepath))
                    log.info(f"DELETE: {filepath}\n")
                else:
                    log.info(f"SAVE (ivar_trim): {filepath}\n")

    stderr.print(f"FILES TO DELETE: {to_delete}\n")
    log.info(f"FILES TO DELETE: {to_delete}")

    for f in to_delete:
        print(f)


if __name__ == "__main__":
    main()
