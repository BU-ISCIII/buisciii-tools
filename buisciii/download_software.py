#!/usr/bin/env python

"""
This module finds and downloads software updates of interest for service templates.
Templates remain unchanged; software candidates, either Singularity images or nf-core
pipelines, still require manual testing.

This download-software module checks the latest downloaded version of a Singularity
image or an nf-core pipeline in the pre-determined directories, then downloads the
latest available version and reports whether the template that employs such software
should be updated or not.

This module can be run in different modes:

- buisciii download-software: will check and, if applicable, download the latest
software version of all the tools that are employed by the service templates.

- buisciii download-software -p XXX -i YYY: will check and, if necessary, download the
  latest software version of the XXX pipeline (-p parameter) and/or the YYY Singularity
  image (-i parameter). More than one image or pipeline can be indicated, separated by
  commas, e.g. -p XXX,ZZZ -i YYY,AAA.

- buisciii download-software --check-only: only checks current template versions and
  writes a TSV report.

- buisciii download-software --dry-run: checks current template versions without writing
  a report or downloading anything. Results from template version checks are only
  displayed in the terminal, nothing else is done.

Singularity images are downloaded from the Galaxy Singularity depot, while nf-core
pipelines are downloaded from GitHub releases. This module uses the nf-core tools CLI to
download pipelines, which requires a micromamba environment with nf-core-tools
installed. The latest nf-core-tools environment available is automatically selected.

By default, downloaded Singularity images are stored in the configured
singularity_images_path (/data/ucct/bi/pipelines/singularity-images), while downloaded
nf-core pipelines are stored in the configured pipelines_path
(/data/ucct/bi/pipelines/nf-core-XXX), differentiated based on the pipeline version.

A log file is stored for each execution of this module in the configured logs_path
(/data/ucct/bi/logs/download_software). If run with the --check-only option, a TSV
report will be generated in the logs_path directory, containing information about the
current and new versions of the software, as well as the status of the download.
"""

import csv
import html.parser
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urljoin

import requests
from packaging.version import InvalidVersion, Version
from rich.console import Console

import buisciii
import buisciii.utils

log = logging.getLogger(__name__)

stderr = Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


@dataclass(frozen=True)
class SingularityImage:
    """Image reference extracted from a service template.

    Attributes:
        name (str): Lowercase software name.
        version (str): Version inferred from the singularity image filename, excluding build tags.
        filename (str): Image reference relative to the configured image folder.
        source_file (str): Service template containing the image of interest.
    """

    name: str
    version: str
    filename: str
    source_file: str


@dataclass(frozen=True)
class GalaxyImage:
    """Singularity image candidate for download taken from the Galaxy index (depot.galaxyproject.org).

    Attributes:
        name (str): Lowercase software name.
        version (str): Version inferred from the filename, excluding build tags.
        filename (str): URL-decoded filename used for the local download.
        url (str): Download URL resolved against the configured index URL.
    """

    name: str
    version: str
    filename: str
    url: str


@dataclass(frozen=True)
class NfCorePipeline:
    """nf-core pipeline reference found while scanning templates.

    Attributes:
        name (str): Lowercase pipeline name without the ``nf-core/`` prefix.
        version (str): Version from the reference or, as a fallback, directory
            names on disk. The fallback need not be the version actually in use.
        source_file (str): Service template containing the pipeline reference.
    """

    name: str
    version: str
    source_file: str


class HrefParser(html.parser.HTMLParser):
    """
    This parser is used to extract download links from the Galaxy Singularity depot index.
    """

    def __init__(self):
        """Initialize the HTML parser as well as an empty link collection."""
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        """Append href values from an anchor encountered by the HTML parser."""
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self.hrefs.append(value)


# The following functions are for general purposes and therefore do not depend on the HPC
# or the service templates. Given that, they are written here without pertaining to any class.
def parse_software_filter(values, option):
    """
    This function returns a set of lowercase names from comma-separated values, in case
    several software names are provided by the user.

    Returns an empty set for absent options. Empty names raise ValueError using
    ``option`` as the label, preventing accidental selection of all software.
    """
    names = set()
    for value in values or ():
        for item in value.split(","):
            name = item.strip().lower()
            if not name:
                raise ValueError(
                    f"{option} requires non-empty names separated by commas"
                )
            names.add(name)
    return names


def parse_version(version):
    """Normalizes a version string and parses it for version comparison."""
    try:
        version = re.sub(r"^v", "", version.strip()).replace("_", ".")
        return Version(version)
    except InvalidVersion:
        return None


def version_is_newer(candidate, current):
    """Compares parsed versions; if either is invalid, treats unequal strings as newer."""
    candidate_version = parse_version(candidate)
    current_version = parse_version(current)
    if candidate_version is not None and current_version is not None:
        return candidate_version > current_version
    return candidate != current


def split_name_version(filename):
    """
    This function extracts the software name and version from a Singularity image reference
    (either from the Galaxy depot or from a service template).

    For instance, 'samtools:1.16.1--h6899075_1' returns ('samtools', '1.16.1').
    The software name is converted to lowercase and the build identifier
    ('--h6899075_1') is not taken into account.

    It also handles paths, URL-encoded characters and .sif/.img extensions.
    Returns (None, None) if the name or version cannot be identified.
    The Singularity image itself is not opened or executed.
    """
    base = os.path.basename(unquote(filename))
    for extension in (".sif", ".img"):
        if base.endswith(extension):
            base = base[: -len(extension)]
            break
    base = base.split("?", 1)[0]
    base = re.sub(r"^depot\.galaxyproject\.org[-_/]singularity[-_/]", "", base)
    base = re.sub(r"^singularity[-_]", "", base)
    base = base.replace("\\:", ":")

    match = re.search(r"[:._-]v?(\d+(?:[._]\d+)*(?:[._-]?(?:alpha|beta|rc)\d*)?)", base)
    if not match:
        return None, None

    name = base[: match.start()]
    version = match.group(1).replace("_", ".")
    name = name.rstrip(":._-")
    if not name:
        return None, None
    return name.lower(), version


def latest_by_name(items):
    """Maps names to the highest-version image or pipeline; retains first on ties."""
    latest = {}
    for item in items:
        current = latest.get(item.name)
        if current is None or version_is_newer(item.version, current.version):
            latest[item.name] = item
    return latest


# Main class to be employed when running this module.
class DownloadSoftware:
    """
    This class is responsible for template discovery, version comparisons, downloads and reports.

    Check-only skips downloads; dry-run also skips report files. Both modes may
    access external services, to wit, the Galaxy singularity depot or nf-core pipelines'
    available versions. The corresponding filters select images, pipelines or both.
    """

    def __init__(
        self,
        conf,
        templates_path=None,
        image=None,
        pipeline=None,
        dry_run=False,
        check_only=False,
    ):
        """
        Load configuration, paths and repeatable comma-separated filters
        (when checking multiple software).

        ``templates_path`` overrides the pre-configured root. ``check_only`` disables
        downloads; ``dry_run`` also disables reports. Invalid filters/cache settings
        raise ValueError; a missing remote inventory raises FileNotFoundError.
        """
        self.conf = conf
        self.settings = conf.get_configuration("download_software") or {}
        data_path = conf.get_configuration("global").get("data_path")

        self.singularity_images_path = Path(
            self.settings.get(
                "singularity_images_path",
                os.path.join(data_path, "pipelines", "singularity-images"),
            )
        )
        self.pipelines_path = Path(
            self.settings.get("pipelines_path", os.path.join(data_path, "pipelines"))
        )
        self.logs_path = Path(
            self.settings.get(
                "logs_path", os.path.join(data_path, "logs", "download_software")
            )
        )
        self.depot_url = self.settings.get(
            "depot_url", "https://depot.galaxyproject.org/singularity/"
        )
        self.nf_core_env = self.settings.get("nf_core_env", "auto")
        self.nf_core_prefix = None
        self.nf_core_cache_mode = self.settings.get("nf_core_cache_mode", "amend")
        self.nf_core_cache_index = self.settings.get("nf_core_cache_index")
        self.nf_core_compress = self.settings.get("nf_core_compress", "none")
        self.nf_core_tools_version = None
        if self.nf_core_cache_mode not in {"amend", "copy", "remote"}:
            raise ValueError(
                "nf_core_cache_mode must be one from these: amend, copy or remote"
            )
        if self.nf_core_cache_mode == "remote":
            if not self.nf_core_cache_index:
                raise ValueError("remote cache mode requires nf_core_cache_index")
            self.nf_core_cache_index = str(
                Path(self.nf_core_cache_index).expanduser().resolve()
            )
            if not Path(self.nf_core_cache_index).is_file():
                raise FileNotFoundError(self.nf_core_cache_index)
        self.templates_path = Path(
            templates_path
            or self.settings.get(
                "templates_path", os.path.join(os.path.dirname(__file__), "templates")
            )
        )
        self.image_filter = parse_software_filter(image, "--image")
        self.pipeline_filter = parse_software_filter(pipeline, "--pipeline")
        self.dry_run = dry_run
        self.check_only = check_only
        self.downloaded_tsv = self.logs_path / "downloaded_software.tsv"

    def handle_download_software(self):
        """
        This function runs the software update check and optional downloads.

        It uses the image and pipeline filters indicated by the user
        to decide what to check. If neither filter is supplied,
        it checks both images and pipelines.

        It finds software references in the templates and calls the methods that
        compare versions and downloads newer candidates when allowed.
        It saves the results to the TSV report unless --dry-run is enabled.

        It performs log completion and returns the combined image and pipeline report rows.
        Each row describes an update found, including its download status.
        """
        self.prepare_logs()
        image_rows = []
        pipeline_rows = []
        if self.image_filter or not self.pipeline_filter:
            images = self.find_current_singularity_images()
            if images:
                galaxy_images = latest_by_name(self.fetch_galaxy_images())
                image_rows = self.process_singularity_images(images, galaxy_images)
                if image_rows:
                    self.append_downloaded_rows(image_rows)
        if self.pipeline_filter or not self.image_filter:
            pipelines = self.find_current_nf_core_pipelines()
            if pipelines:
                pipeline_rows = self.process_nf_core_pipelines(
                    latest_by_name(pipelines).values()
                )
                if pipeline_rows:
                    self.append_downloaded_rows(pipeline_rows)

        rows = image_rows + pipeline_rows
        downloaded = sum(row["status"] == "downloaded" for row in rows)
        if self.check_only or self.dry_run:
            log.info(
                "Software check completed successfully; no downloads were performed."
            )
        else:
            log.info(
                "Software download run completed successfully. Successful downloads: %s.",
                downloaded,
            )
        stderr.print(
            f"[green]\nDOWNLOAD-SOFTWARE has finished. Log directory: {self.logs_path}",
            highlight=False,
        )
        return rows

    def prepare_logs(self):
        """
        Creates the log directory unless dry-run is specified, and log configured paths.
        If this log folder exists already, it is not removed or modified.
        """
        if not self.dry_run:
            self.logs_path.mkdir(parents=True, exist_ok=True)
        log.info("Singularity images path: %s", self.singularity_images_path)
        log.info("Pipelines path: %s", self.pipelines_path)
        log.info("Templates path: %s", self.templates_path)

    def iter_template_files(self):
        """
        Finds files in the configured templates directory and all its subdirectories,
        without performing any filtering or looking for specific files or patterns.
        It yields each file path one at a time, skipping directories.
        Raises FileNotFoundError if the templates directory does not exist.
        """
        if not self.templates_path.exists():
            raise FileNotFoundError(
                f"Templates path does not exist: {self.templates_path}"
            )
        for path in self.templates_path.rglob("*"):
            if path.is_file():
                yield path

    def find_current_singularity_images(self):
        """Returns filtered image references parsed from service template contents."""
        pattern = re.compile(
            rf"{re.escape(str(self.singularity_images_path))}/([^\s\"']+)"
        )
        images = {}
        for path in self.iter_template_files():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError as exc:
                log.warning("Could not read %s: %s", path, exc)
                continue
            for match in pattern.finditer(text):
                filename = match.group(1).rstrip(";&)")
                name, version = split_name_version(filename)
                if not name or not version:
                    log.debug("Could not parse image reference: %s", filename)
                    continue
                if self.image_filter and name not in self.image_filter:
                    continue
                image = SingularityImage(name, version, filename, str(path))
                key = (image.name, image.version, image.filename)
                images[key] = image
        stderr.print(f"[yellow]Found {len(images)} Singularity image references.")
        return sorted(images.values(), key=lambda item: (item.name, item.version))

    def fetch_galaxy_images(self):
        """Lists Singularity images available in the Galaxy repository.

        Reads the links on the repository's HTML page and extracts each image's
        software name, version, filename and download URL.
        Skips entries whose name or version cannot be identified.
        If --image is supplied, this function includes only the requested software names.

        Returns a list of GalaxyImage objects. This function does not compare
        versions with the templates or download image files.
        """
        stderr.print(f"[yellow]Fetching Galaxy Singularity index: {self.depot_url}")
        response = requests.get(self.depot_url, timeout=60)
        response.raise_for_status()
        parser = HrefParser()
        parser.feed(response.text)

        images = []
        for href in parser.hrefs:
            filename = os.path.basename(unquote(href))
            if not filename or filename.endswith("/"):
                continue
            name, version = split_name_version(filename)
            if not name or not version:
                continue
            if self.image_filter and name not in self.image_filter:
                continue
            images.append(
                GalaxyImage(name, version, filename, urljoin(self.depot_url, href))
            )
        log.info("Found %s Galaxy image candidates", len(images))
        return images

    def process_singularity_images(self, current_images, galaxy_images):
        """
        Compares image versions used in templates with those available on Galaxy.

        Downloads newer versions unless --check-only or --dry-run are enabled.
        If the image already exists in the destination folder, this function marks it as
        'already_downloaded'; its contents are not checked.

        Returns report rows with the current version, newer version, destination
        and download status. Stops processing if a download fails.
        """
        rows = []
        for image in current_images:
            candidate = galaxy_images.get(image.name)
            if candidate is None:
                log.warning("No Galaxy candidate found for %s", image.filename)
                continue
            if not version_is_newer(candidate.version, image.version):
                if parse_version(candidate.version) == parse_version(image.version):
                    log.info(
                        "Template already uses the latest available version: %s %s (source: %s)",
                        image.name,
                        image.version,
                        image.source_file,
                    )
                else:
                    log.info(
                        "No newer Galaxy version found for template reference: %s %s "
                        "(Galaxy candidate: %s; template: %s)",
                        image.name,
                        image.version,
                        candidate.version,
                        image.source_file,
                    )
                continue
            destination = self.singularity_images_path / candidate.filename
            status = "newer_available"
            if destination.exists():
                status = "already_downloaded"
            elif not self.check_only and not self.dry_run:
                self.download_file(candidate.url, destination)
                status = "downloaded"
            elif self.dry_run:
                status = "dry_run"

            row = {
                "date": datetime.now().isoformat(timespec="seconds"),
                "type": "singularity",
                "name": image.name,
                "current_version": image.version,
                "new_version": candidate.version,
                "current_reference": image.filename,
                "downloaded_reference": str(destination),
                "source_file": image.source_file,
                "status": status,
            }
            rows.append(row)
            stderr.print(
                f"{image.name}: {image.version} -> {candidate.version} ({status})"
            )
            log.info("%s", row)
        return rows

    def download_file(self, url, destination):
        """
        Downloads a Singularity image from an URL to the destination path.

        This function downloads the software to a temporary .part
        file in the same folder, and then renames it to the
        final filename only after the download finishes successfully.

        If the download fails, it raises an error.
        Downloads are not retried and checksums are not verified.
        """
        self.singularity_images_path.mkdir(parents=True, exist_ok=True)
        tmp_destination = destination.with_suffix(destination.suffix + ".part")
        stderr.print(f"Downloading {url} to {destination}")
        with requests.get(url, stream=True, timeout=120) as response:
            response.raise_for_status()
            with tmp_destination.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fh.write(chunk)
        tmp_destination.replace(destination)

    def find_current_nf_core_pipelines(self):
        """
        Finds nf-core pipelines indicated in the service templates.
        Extracts each pipeline's name and version from its path in the template.

        Applies the requested pipeline filter and returns unique name/version pairs,
        keeping a source template path for each pair.
        Skips references whose version cannot be determined.
        """
        pattern = re.compile(
            rf"{re.escape(str(self.pipelines_path))}/nf-core-([A-Za-z0-9_.-]+)[^\s\"'\\]*"
        )
        version_pattern = re.compile(r"nf-core-[A-Za-z0-9_.-]+[-_](\d+(?:[._]\d+)*)")
        pipelines = {}
        for path in self.iter_template_files():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError as exc:
                log.warning("Could not read %s: %s", path, exc)
                continue
            for match in pattern.finditer(text):
                raw_name = match.group(1).split("/", 1)[0]
                name = re.sub(r"[-_]\d.*$", "", raw_name).lower()
                version_match = version_pattern.search(match.group(0))
                version = (
                    version_match.group(1).replace("_", ".") if version_match else None
                )
                if version is None:
                    version = self.find_pipeline_version_on_disk(name)
                if version is None:
                    log.warning(
                        "Could not detect nf-core version for %s in %s", name, path
                    )
                    continue
                if self.pipeline_filter and name not in self.pipeline_filter:
                    continue
                pipeline = NfCorePipeline(name, version, str(path))
                pipelines[(pipeline.name, pipeline.version)] = pipeline
        stderr.print(f"[yellow]\nFound {len(pipelines)} nf-core pipeline references.")
        return sorted(pipelines.values(), key=lambda item: (item.name, item.version))

    def find_pipeline_version_on_disk(self, name):
        """
        Returns the highest version available in the nf-core pipelines' directory
        inferred from the pipeline dirnames.
        """
        pipeline_dir = self.pipelines_path / f"nf-core-{name}"
        if not pipeline_dir.exists():
            return None
        versions = []
        for child in pipeline_dir.iterdir():
            if not child.is_dir():
                continue
            match = re.search(
                rf"nf-core-{re.escape(name)}[-_](\d+(?:[._]\d+)*)", child.name
            )
            if match:
                versions.append(match.group(1).replace("_", "."))
        if not versions:
            return None
        return sorted(
            versions, key=lambda version: parse_version(version) or Version("0")
        )[-1]

    def process_nf_core_pipelines(self, pipelines):
        """
        Checks for newer releases of the detected nf-core pipeline/s.

        For each newer release, this function checks whether its directory already exists.
        If it does, marks it as 'already_downloaded' without checking its contents.
        Otherwise, downloads it unless --check-only or --dry-run are enabled.
        Both checking modes show the planned download command.

        Returns report rows for newer releases, including the detected version,
        new version, destination, source template and download status.
        Stops processing if a network request or command fails.
        """
        rows = []
        for pipeline in pipelines:
            latest = self.fetch_latest_nf_core_version(pipeline.name)
            if latest is None:
                continue
            if not version_is_newer(latest, pipeline.version):
                log.info(
                    "nf-core/%s is up to date: %s", pipeline.name, pipeline.version
                )
                continue
            existing = self.find_nf_core_version(pipeline.name, latest)
            destination = existing or self.nf_core_destination(pipeline.name, latest)
            if existing is not None:
                status = "already_downloaded"
            elif not self.check_only and not self.dry_run:
                self.download_nf_core_pipeline(pipeline.name, latest)
                status = "downloaded"
            elif self.dry_run:
                status = "dry_run"
            else:
                status = "newer_available"
            if self.check_only or self.dry_run:
                self.select_nf_core_environment()
                self.show_nf_core_command(pipeline.name, latest)
            row = {
                "date": datetime.now().isoformat(timespec="seconds"),
                "type": "nf-core",
                "name": pipeline.name,
                "current_version": pipeline.version,
                "new_version": latest,
                "current_reference": f"nf-core/{pipeline.name}",
                "downloaded_reference": str(destination),
                "source_file": pipeline.source_file,
                "status": status,
            }
            rows.append(row)
            stderr.print(
                f"nf-core/{pipeline.name}: {pipeline.version} -> {latest} ({status})"
            )
            log.info("%s", row)
        return rows

    def fetch_latest_nf_core_version(self, name):
        """Returns the latest release tag reported by GitHub, without leading v."""
        url = f"https://api.github.com/repos/nf-core/{name}/releases/latest"
        response = requests.get(url, timeout=60)
        if response.status_code == 404:
            log.warning("nf-core/%s not found in GitHub releases", name)
            return None
        response.raise_for_status()
        tag_name = response.json().get("tag_name")
        if not tag_name:
            log.warning("Could not detect latest release for nf-core/%s", name)
            return None
        return tag_name.lstrip("v")

    def find_nf_core_version(self, name, version):
        """
        This function finds an existing directory for the nf-core pipeline version of interest.

        It searches directly inside <pipelines_path>/nf-core-<name>/.
        Accepts subdirectory names such as 'nf-core-XXX_3.10.0',
        'nf-core-XXX-3.10.0' or '3.10.0'. Version components may also
        be separated by underscores.

        Returns the first matching directory path, or None if none exists.
        Only the directory name is checked, not its contents or completeness.
        """
        pipeline_dir = self.pipelines_path / f"nf-core-{name}"
        if not pipeline_dir.exists():
            return None
        version_token = re.escape(version).replace(r"\.", "[._]")
        pattern = re.compile(rf"(?:nf-core-{re.escape(name)}[-_])?{version_token}")
        for child in sorted(pipeline_dir.iterdir()):
            if child.is_dir() and pattern.fullmatch(child.name):
                return child
        return None

    def nf_core_destination(self, name, version):
        """
        Returns the Path for a new pipeline download without creating it,
        with the proper name and version subdirectory.
        """
        return self.pipelines_path / f"nf-core-{name}" / f"nf-core-{name}_{version}"

    def select_nf_core_environment(self):
        """Selects the highest stable nf-core-tools micromamba environment prefix."""
        if self.nf_core_env != "auto" or self.nf_core_prefix is not None:
            return
        if shutil.which("micromamba") is None:
            raise RuntimeError(
                "micromamba command not found; automatic nf-core selection requires it to be installed"
            )
        result = subprocess.run(
            ["micromamba", "env", "list", "--json"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        environments = json.loads(result.stdout)["envs"]
        candidates = []
        # Inspect installed package metadata, not the version in the directory name.
        script = "import json; from importlib.metadata import version; print(json.dumps(version('nf-core')))"
        for prefix in sorted(set(environments)):
            path = Path(prefix)
            if path.name != "nf-core" and not path.name.startswith("nf-core-"):
                continue
            try:
                result = subprocess.run(
                    [
                        "micromamba",
                        "run",
                        "-p",
                        str(path),
                        str(path / "bin" / "python"),
                        "-c",
                        script,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                version = Version(json.loads(result.stdout))
            except (subprocess.SubprocessError, OSError, ValueError, TypeError) as exc:
                log.warning("Cannot inspect nf-core environment %s: %s", path, exc)
                stderr.print(
                    f"Skipping nf-core environment {path}: {exc}", markup=False
                )
                continue
            log.info("Installed nf-core candidate: %s (%s)", path, version)
            if version.is_prerelease or version.is_devrelease:
                log.info("Skipping non-stable nf-core version: %s (%s)", path, version)
                continue
            candidates.append((version, str(path)))
        if not candidates:
            raise RuntimeError(
                "No installed stable nf-core-tools found in micromamba nf-core* environments!"
            )
        version, self.nf_core_prefix = max(candidates)
        message = f"[yellow]Selected nf-core environment: {self.nf_core_prefix}; installed version: {version}"
        stderr.print(message)
        log.info(message)

    def check_nf_core_tools(self):
        """
        Prepares the micromamba environment, verifies required CLI flags and returns version output.

        Caches successful validation. Missing tools/options raise RuntimeError;
        subprocess errors propagate. This does not test pipeline compatibility.
        """
        if self.nf_core_tools_version is not None:
            return self.nf_core_tools_version
        if shutil.which("micromamba") is None:
            raise RuntimeError("micromamba command not found")
        self.select_nf_core_environment()
        prefix = self.nf_core_command_prefix()
        result = subprocess.run(
            prefix + ["--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        version = (result.stdout + result.stderr).strip()
        help_result = subprocess.run(
            prefix + ["pipelines", "download", "--help"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        help_text = help_result.stdout + help_result.stderr
        required = [
            "--revision",
            "--outdir",
            "--container-system",
            "--container-cache-utilisation",
            "--compress",
        ]
        if self.nf_core_cache_mode == "remote":
            required.append("--container-cache-index")
        missing = [option for option in required if option not in help_text]
        if missing:
            raise RuntimeError(
                f"nf-core in environment {self.nf_core_prefix or self.nf_core_env} lacks options: {', '.join(missing)}"
            )
        self.nf_core_tools_version = version
        selected = self.nf_core_prefix or self.nf_core_env
        log.info("nf-core environment: %s; tools version: %s", selected, version)
        stderr.print(
            f"nf-core environment: {selected}; tools version: {version}", markup=False
        )
        return version

    def nf_core_command_prefix(self):
        """
        Returns launch arguments for the further nf-core pipeline executing, without
        actually running it.
        """
        if self.nf_core_env == "auto" and self.nf_core_prefix is None:
            raise RuntimeError(
                "Select the nf-core environment before building a command"
            )
        if self.nf_core_prefix is not None:
            return ["micromamba", "run", "-p", self.nf_core_prefix, "nf-core"]
        return ["micromamba", "run", "-n", self.nf_core_env, "nf-core"]

    def build_nf_core_command(self, name, version):
        """
        Returns pipelines download arguments using the most recent nf-core tools
        micromamba environment available, without executing.
        """
        command = self.nf_core_command_prefix() + [
            "pipelines",
            "download",
            f"nf-core/{name}",
            "--revision",
            version,
            "--outdir",
            str(self.nf_core_destination(name, version)),
            "--container-system",
            "singularity",
            "--container-cache-utilisation",
            self.nf_core_cache_mode,
            "--compress",
            self.nf_core_compress,
        ]
        if self.nf_core_cache_mode == "remote":
            command.extend(["--container-cache-index", self.nf_core_cache_index])
        return command

    def nf_core_environment(self):
        """
        Prepares environment variables for the nf-core pipelines download command.

        This function copies the current environment and sets NXF_SINGULARITY_CACHEDIR to the
        configured Singularity images directory. It returns the resulting dictionary
        without modifying the current terminal environment.
        """
        env = os.environ.copy()
        env["NXF_SINGULARITY_CACHEDIR"] = str(
            self.singularity_images_path.expanduser().resolve()
        )
        return env

    def show_nf_core_command(self, name, version):
        """Prints and logs the planned command and cache assignment without executing."""
        description = "NXF_SINGULARITY_CACHEDIR={} {}".format(
            shlex.quote(self.nf_core_environment()["NXF_SINGULARITY_CACHEDIR"]),
            shlex.join(self.build_nf_core_command(name, version)),
        )
        stderr.print("Planned command: " + description, markup=False)
        log.info("Planned command: %s", description)

    def download_nf_core_pipeline(self, name, version):
        """
        Downloads a release and stream stdout/stderr to the general and individual logs.

        Rejects existing destinations with FileExistsError. Validation, I/O and
        subprocess errors propagate; failures may leave partial files. Exit code zero
        is not a functional test. The caller must enforce dry-run/check-only.
        """
        destination = self.nf_core_destination(name, version)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(
                f"Refusing to overwrite existing nf-core destination: {destination}"
            )
        tools_version = self.check_nf_core_tools()
        command = self.build_nf_core_command(name, version)
        env = self.nf_core_environment()
        Path(env["NXF_SINGULARITY_CACHEDIR"]).mkdir(parents=True, exist_ok=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.show_nf_core_command(name, version)
        stderr.print("Running: " + shlex.join(command), markup=False)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        log_filepath = self.logs_path / "{}_{}_{}.log".format(
            name, version, datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        log.info("nf-core/%s %s output log: %s", name, version, log_filepath)
        with log_filepath.open("w", encoding="utf-8") as log_fh:
            log_fh.write(
                f"nf-core environment: {self.nf_core_prefix or self.nf_core_env}\n{tools_version}\n"
            )
            log_fh.write(
                f"NXF_SINGULARITY_CACHEDIR={env['NXF_SINGULARITY_CACHEDIR']}\n"
            )
            log_fh.write("Command: " + shlex.join(command) + "\n")
            log_fh.flush()
            try:
                with subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                ) as process:
                    for line in process.stdout:
                        log_fh.write(line)
                        log_fh.flush()
                        log.info(
                            "[nf-core/%s %s] %s", name, version, line.rstrip("\r\n")
                        )
                    returncode = process.wait()
                if returncode != 0:
                    raise subprocess.CalledProcessError(returncode, command)
            except Exception as exc:
                message = f"nf-core/{name} {version} download failed: {exc}. Check log for details: {log_filepath}. Download folder may be incomplete."
                log.error(message)
                log_fh.write(message + "\n")
                raise
            message = f"nf-core/{name} {version} download completed successfully!. Destination: {destination}"
            log.info(message)
            log_fh.write(message + "\n")

    def append_downloaded_rows(self, rows):
        """Appends report dictionaries to the cumulative TSV unless dry-run being specified by the user."""
        if self.dry_run:
            return
        self.logs_path.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "date",
            "type",
            "name",
            "current_version",
            "new_version",
            "current_reference",
            "downloaded_reference",
            "source_file",
            "status",
        ]
        write_header = not self.downloaded_tsv.exists()
        with self.downloaded_tsv.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
            if write_header:
                writer.writeheader()
            writer.writerows(rows)
