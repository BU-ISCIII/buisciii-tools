#!/usr/bin/env python

# Generic imports
from datetime import datetime
import logging
import rich.console
import os
import sys
import jinja2
import markdown
import pdfkit
import PyPDF2

# Local imports
import bu_isciii.utils
import bu_isciii.config_json
import bu_isciii.drylab_api
import bu_isciii.service_json

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
        path=None,
        ask_path=False,
    ):
        if type is None:
            self.type = bu_isciii.utils.prompt_selection(
                msg="Select the documentation type you want to create",
                choices=["service_info", "delivery"],
            )
        self.doc_conf = bu_isciii.config_json.ConfigJson().get_configuration(
            "bioinfo_doc"
        )
        if path is None:
            if ask_path:
                self.path = bu_isciii.utils.prompt_path(
                    msg="Path where bioinfo_doc folder is mounted in your local WS."
                )
            else:
                self.path = os.path.normpath(self.doc_conf["bioinfodoc_path"])
        else:
            self.path = path
        if not os.path.exists(self.path):
            stderr.print("[red] Folder does not exist. " + self.path + "!")
            sys.exit(1)
        if resolution_id is None:
            self.resolution_id = bu_isciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id
        conf_api = bu_isciii.config_json.ConfigJson().get_configuration(
            "local_api_settings"
        )
        rest_api = bu_isciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"]
        )
        resolution_info = rest_api.get_request(
            "resolutionFullData", "resolution", self.resolution_id
        )
        # TODO: When delivery info can be downloaded from iSkyLIMS
        # resolution_info = rest_api.get_request(
        #    "resolutionFullData", "delivery", self.resolution_id
        # )
        if not resolution_info:
            stderr.print(
                "[red] Unable to fetch information for resolution "
                + self.resolution_id
                + "!"
            )
            sys.exit(1)
        resolution_folder = resolution_info["Resolutions"]["resolutionFullNumber"]
        self.resolution = resolution_info["Resolutions"]
        self.resolution_id = resolution_info["Resolutions"]["resolutionFullNumber"]
        self.resolution_number = resolution_info["Resolutions"]["resolutionNumber"]
        self.delivery_number = self.resolution_number.partition(".")[2]
        resolution_date = self.resolution.get("resolutionDate")
        self.resolution_datetime = datetime.strptime(resolution_date, "%Y-%m-%d")
        year = datetime.strftime(self.resolution_datetime, "%Y")
        self.service_folder = os.path.join(
            self.path, self.doc_conf["services_path"], year, resolution_folder
        )
        self.samples = resolution_info["Samples"]
        self.user_data = resolution_info["Service"]["serviceUserId"]
        self.service = resolution_info["Service"]
        self.handled_services = None
        path_to_wkhtmltopdf = os.path.normpath(self.doc_conf["wkhtmltopdf_path"])
        self.config_pdfkit = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
        if self.type == "service_info":
            self.template_file = self.doc_conf["service_info_template_path_file"]
        else:
            self.template_file = self.doc_conf["delivery_template_path_file"]
        self.services_requested = resolution_info["Resolutions"]["availableServices"]

    def create_structure(self):
        if os.path.exists(self.service_folder):
            log.info("Already creted the service folder for %s", self.resolution_id)
            stderr.print(
                "[green] Skiping folder creation for service "
                + self.resolution_id
                + ". Trying with subfolders"
            )
            for folder in self.doc_conf["service_folder"]:
                if os.path.exists(os.path.join(self.service_folder, folder)):
                    log.info(
                        "Already creted the service subfolders for %s",
                        self.resolution_id,
                    )
                    stderr.print(
                        "[green] Skiping folder creation for service "
                        + self.resolution_id
                        + "/"
                        + folder
                    )
                else:
                    log.info("Creating service subfolder %s", folder)
                    stderr.print(
                        "[blue] Creating the service subfolderfolder "
                        + folder
                        + " for "
                        + self.resolution_id
                        + "!"
                    )
                    os.makedirs(
                        os.path.join(self.service_folder, folder), exist_ok=True
                    )
                    log.info("Service folders created")
                if self.type == "delivery":
                    file_path = os.path.join(self.service_folder, "result")
                    delivery_date = self.resolution.get("resolutionDeliveryDate")
                    delivery_datetime = datetime.strptime(delivery_date, "%Y-%m-%d")
                    delivery_date_folder = datetime.strftime(
                        delivery_datetime, "%Y%m%d"
                    )
                    self.delivery_sub_folder = (
                        str(delivery_date_folder)
                        + "_entrega"
                        + self.delivery_number.zfill(2)
                    )
                    os.makedirs(
                        os.path.join(file_path, self.delivery_sub_folder), exist_ok=True
                    )

        else:
            log.info("Creating service folder for %s", self.resolution_id)
            stderr.print(
                "[blue] Creating the service folder for " + self.resolution_id + "!"
            )
            for folder in self.doc_conf["service_folder"]:
                os.makedirs(os.path.join(self.service_folder, folder), exist_ok=True)
            log.info("Service folders created")
        return

    def create_markdown(self, file_path):
        """Create the markdown fetching the information from request api"""
        log.info(
            "starting proccess to create markdown for service %s", self.resolution_id
        )
        stderr.print("[green] Creating markdown file for " + self.resolution_id + " !")
        log.info("Start creating the markdown file")
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
        markdown_data["resolution"] = self.resolution
        f_name = self.resolution_number + ".md"
        file_name = os.path.join(file_path, f_name)
        file_name = os.path.join(file_path, f_name)

        # Delivery related information
        markdown_data["service_notes"] = (
            self.service["serviceNotes"].replace("\r", "").replace("\n", " ")
        )

        pakage_path = os.path.dirname(os.path.realpath(__file__))
        templateLoader = jinja2.FileSystemLoader(searchpath=pakage_path)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(self.template_file)
        # Create markdown
        mk_text = template.render(markdown_data)

        with open(file_name, "wb") as fh:
            fh.write(mk_text.encode("utf-8"))
        log.info("Creation the markdown file is completed")
        return str(mk_text), file_name

    def convert_markdown_to_html(self, mk_text):
        html_text = markdown.markdown(
            mk_text,
            extensions=[
                "pymdownx.extra",
                "pymdownx.b64",
                "pymdownx.highlight",
                "pymdownx.emoji",
                "pymdownx.tilde",
            ],
            extension_configs={
                "pymdownx.b64": {
                    "base_path": os.path.dirname(os.path.realpath(__file__))
                },
                "pymdownx.highlight": {"noclasses": True},
            },
        )
        return html_text

    def wrap_html(self, html_text, file_name):
        file_name += ".html"
        html_template_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            self.doc_conf["html_template_path_file"],
        )
        css_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), self.doc_conf["path_to_css"]
        )
        with open(html_template_file, "r") as fh:
            file_read = fh.read()
        file_read = file_read.replace("{text_to_add}", html_text)
        file_read = file_read.replace("{path_to_css}", css_path)
        with open(file_name, "w") as fh:
            fh.write(file_read)
        return file_name

    def convert_to_pdf(self, html_file):
        pdf_file = html_file.replace(".html", ".pdf")
        try:
            pdfkit.from_file(
                html_file, output_path=pdf_file, configuration=self.config_pdfkit
            )
        except OSError as e:
            stderr.print("[red] Unable to convert to PDF")
            log.exception("Unable to create pdf.", exc_info=e)
        return

    def generate_documentation_files(self, type):
        if type == "service_info":
            file_path = os.path.join(self.service_folder, "service_info")
        elif type == "delivery":
            file_path = os.path.join(
                self.service_folder, "result", self.delivery_sub_folder
            )
        else:
            stderr.print("[red] invalid option")
            log.error("Unable to generate files because invalid option %s", type)
            sys.exit(1)

        mk_text, file_name = self.create_markdown(file_path)
        file_name_without_ext = file_name.replace(".md", "")
        html_text = self.convert_markdown_to_html(mk_text)
        html_file_name = self.wrap_html(html_text, file_name_without_ext)
        self.convert_to_pdf(html_file_name)
        pdf_file = html_file_name.replace(".html", ".pdf")
        return pdf_file

    def join_pdf_files(self, service_pdf, result_template, out_file):
        mergeFile = PyPDF2.PdfFileMerger()
        mergeFile.append(PyPDF2.PdfFileReader(service_pdf, "rb"))
        mergeFile.append(PyPDF2.PdfFileReader(result_template, "rb"))
        mergeFile.write(out_file)
        return

    def create_delivery_doc(self, resolution_pdf):
        """Get the service pdf file from the requested service"""
        services_ids = bu_isciii.utils.get_service_ids(self.services_requested)
        services_json = bu_isciii.service_json.ServiceJson()

        if len(services_ids) == 1:
            try:
                service_pdf = services_json.get_find(services_ids[0], "delivery_pdf")
            except KeyError as e:
                stderr.print(
                    "[red]ERROR: Service id %s not found in services json file."
                    % services_ids[0]
                )
                stderr.print("traceback error %s" % e)
                sys.exit()
            try:
                real_path = os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), service_pdf
                )
                delivery_pdf_name = (
                    self.resolution_number + "_" + self.delivery_sub_folder + ".pdf"
                )
                delivery_pdf_file = os.path.join(
                    self.service_folder,
                    "result",
                    self.delivery_sub_folder,
                    delivery_pdf_name,
                )
                self.join_pdf_files(resolution_pdf, real_path, delivery_pdf_file)
                stderr.print(
                    "[green]Successfully merged the PDFs %s and %s to the directory %s"
                    % (
                        resolution_pdf,
                        service_pdf,
                        os.path.join(
                            self.service_folder,
                            "result",
                            self.delivery_sub_folder,
                            "delivery.pdf",
                        ),
                    ),
                    highlight=False,
                )

            except OSError as e:
                stderr.print("[red]ERROR: Merging PDFs failed.")
                stderr.print("traceback error %s" % e)
                sys.exit()
        else:
            stderr.print(
                "[red] ERROR: I'm not already prepared for handling more than one error at the same time, sorry! Please re-run and select one of the service ids."
            )
            sys.exit()
            return False
        return None

    def create_documentation(self):
        self.create_structure()
        if self.type == "service_info":
            self.generate_documentation_files("service_info")
            return
        elif self.type == "delivery":
            pdf_resolution = self.generate_documentation_files("delivery")
            self.create_delivery_doc(pdf_resolution)
            return
        else:
            stderr.print("[red] invalid option")
            log.error("Unable to proceed because invalid option %s", type)
            sys.exit(1)
