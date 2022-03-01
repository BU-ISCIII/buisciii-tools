#!/usr/bin/env python
from datetime import datetime
import logging
import rich.console
import re
import os
import sys
import jinja2
import markdown

import bu_isciii.utils
import bu_isciii.config_json
import bu_isciii.drylab_api

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=bu_isciii.utils.rich_force_colors(),
)


class BioinfoDoc:
    def __init__(
        self,
        type=None,
        resolution_id=None,
        local_folder=None,
    ):
        if type is None:
            self.type = bu_isciii.utils.prompt_selection(
                msg="Select the documentation type you want to create",
                choices=["resolution", "delivery"],
            )
        if local_folder is None:
            self.local_folder = bu_isciii.utils.prompt_path(
                msg="Path where bioinfo folder is mounted"
            )
        else:
            self.local_folder = local_folder
        if not os.path.exists(self.local_folder):
            stderr.print("[red] Folder does not exist. " + self.local_folder + "!")
            sys.exit(1)
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id
        self.config_doc = bu_isciii.config_json.ConfigJson().get_configuration(
            "bioinfo_doc"
        )
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration("api_settings")
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )
        resolution_info = rest_api.get_request(
            "resolutionFullData", "resolution", self.resolution_id
        )
        if not resolution_info:
            stderr.print(
                "[red] Unable to fetch information for resolution "
                + self.resolution_id
                + "!"
            )
            sys.exit(1)
        resolution_folder = resolution_info["Resolutions"]["resolutionFullNumber"]
        year = str(datetime.now().year)
        self.service_folder = os.path.join(
            self.local_folder, self.config_doc["services_path"], year, resolution_folder
        )
        self.resolution = resolution_info["Resolutions"]
        self.resolution_id = resolution_info["Resolutions"]["resolutionFullNumber"]
        self.samples = resolution_info["Samples"]
        self.user_data = resolution_info["Service"]["serviceUserId"]
        self.service = resolution_info["Service"]

    def create_structure(self):
        if os.path.exists(self.service_folder):
            log.info("Already creted the service folder for %s", self.resolution_id)
            stderr.print(
                "[green] Skiping folder creation for service "
                + self.resolution_id
                + "!"
            )
            return
        else:
            log.info("Creating service folder for %s", self.resolution_id)
            stderr.print(
                "[blue] Creating the service folder for " + self.resolution_id + "!"
            )
            for folder in self.config_doc["service_folder"]:
                os.makedirs(os.path.join(self.service_folder, folder), exist_ok=True)
            log.info("Service folders created")
        return

    def create_markdown(self, file_path):
        """Create the markdown fetching the information from request api"""
        markdown_data = {}
        # service related information
        markdown_data["service"] = self.service
        markdown_data["user_data"] = self.user_data
        samples_in_service = {}
        for sample_data in self.samples:
            if sample_data["runName"] not in samples_in_service:
                samples_in_service[sample_data["runName"]] = {}
            if (
                sample_data["projectName"]
                not in samples_in_service[sample_data["runName"]]
            ):
                samples_in_service[sample_data["runName"]][
                    sample_data["projectName"]
                ] = []
            samples_in_service[sample_data["runName"]][
                sample_data["projectName"]
            ].append(sample_data["sampleName"])
        markdown_data["samples"] = samples_in_service

        # Resolution related information
        if "request" not in file_path:
            markdown_data["resolution"] = self.resolution
        # Delivery related information

        markdown_data["service_notes"] = (
            self.service["serviceNotes"].replace("\r", "").replace("\n", " ")
        )

        template_file = self.config_doc["template_path_file"]
        pakage_path = os.path.dirname(os.path.realpath(__file__))
        templateLoader = jinja2.FileSystemLoader(searchpath=pakage_path)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(template_file)
        # Create markdown

        outputText = template.render(markdown_data)
        import pdb

        pdb.set_trace()
        """
        md_name = "INFRES_" + json_data["service_number"] + ".md"
        file = open(md_name, "wb")
        file.write(outputText.encode("utf-8"))
        file.close()
        """
        return

    def convert_markdown(self, md_name):
        input_md = open(md_name, mode="r", encoding="utf-8").read()
        converted_md = markdown.markdown(
            "[TOC]\n" + input_md,
            extensions=[
                "pymdownx.extra",
                "pymdownx.b64",
                "pymdownx.highlight",
                "pymdownx.emoji",
                "pymdownx.tilde",
                "toc",
            ],
            extension_configs={
                "pymdownx.b64": {"base_path": os.path.dirname(md_name)},
                "pymdownx.highlight": {"noclasses": True},
                "toc": {"title": "Table of Contents"},
            },
        )

        return converted_md, md_name

    def wrap_html(self, converted_md, md_name):
        header = """<!DOCTYPE html><html>
        <head>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
            <style>
                body {
                font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji";
                padding: 3em;
                margin-right: 350px;
                max-width: 100%;
                }
                .toc {
                position: fixed;
                right: 20px;
                width: 300px;
                padding-top: 20px;
                overflow: scroll;
                height: calc(100% - 3em - 20px);
                }
                .toctitle {
                font-size: 1.8em;
                font-weight: bold;
                }
                .toc > ul {
                padding: 0;
                margin: 1rem 0;
                list-style-type: none;
                }
                .toc > ul ul { padding-left: 20px; }
                .toc > ul > li > a { display: none; }
                img { max-width: 800px; }
                pre {
                padding: 0.6em 1em;
                }
                h2 {
                }
            </style>
        </head>
        <body>
        <div class="container">
        """
        footer = """
        </div>
        </body>
        </html>
        """

        html = header + converted_md[0] + footer
        html_name = "nombre_provisional.html"
        file = open(html_name, "w")
        file.write(html)
        file.close()

        return True

    def create_resolution_doc(self):
        # check if request service documentation was created
        if not os.listdir(os.path.join(self.service_folder, "request")):
            file_path = os.path.join(self.service_folder, "request")
            # self.create_resolution_doc(file_path)
            md_name = self.create_markdown(file_path)
        converted_md = self.convert_markdown(md_name)
        self.wrap_html(converted_md, md_name)
        return

    def create_documentation(self):
        self.create_structure()
        # file_folder = os.path.join(self.service_folder, self.type)
        # file_name = os.path.join(file_folder)
        if self.type == "resolution":
            self.create_resolution_doc()
            return
        if self.type == "delivery":
            self.create_delivery()
            return
