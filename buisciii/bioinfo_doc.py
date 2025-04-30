#!/usr/bin/env python

# Generic imports
from datetime import datetime
import logging
import rich.console
import os
import re
import sys
import jinja2
import markdown
import pdfkit
import PyPDF2
import yaml
import subprocess
import json
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from smtplib import SMTP
import ssl

# Local imports
import buisciii.utils
import buisciii.config_json
import buisciii.drylab_api
import buisciii.service_json

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


class BioinfoDoc:
    def __init__(
        self,
        type=None,
        resolution_id=None,
        path=None,
        ask_path=False,
        sftp_folder=False,
        report_md=False,
        results_md=False,
        api_user=None,
        api_password=None,
        conf=None,
        email_psswd=None,
    ):
        if type is None:
            self.type = buisciii.utils.prompt_selection(
                msg="Select the documentation type you want to create",
                choices=["service_info", "delivery"],
            )
        self.conf = conf.get_configuration("bioinfo_doc")
        if path is None:
            if ask_path:
                self.path = buisciii.utils.prompt_path(
                    msg="Path where bioinfo_doc folder is mounted in your local WS."
                )
            else:
                self.path = os.path.normpath(self.conf["bioinfodoc_path"])
        else:
            self.path = path
        if not os.path.exists(self.path):
            stderr.print("[red] Folder does not exist. " + self.path + "!")
            sys.exit(1)
        if resolution_id is None:
            self.resolution_id = buisciii.utils.prompt_resolution_id()
        else:
            self.resolution_id = resolution_id
        conf_api = conf.get_configuration("api_settings")
        self.rest_api = buisciii.drylab_api.RestServiceApi(
            conf_api["server"], conf_api["api_url"], api_user, api_password
        )
        self.resolution_info = self.rest_api.get_request(
            request_info="service-data", safe=True, resolution=self.resolution_id
        )
        if self.resolution_info == 404:
            print("Received Error 404 from Iskylims API. Aborting")
            sys.exit(1)
        if self.type == "delivery":
            if len(self.resolution_info["resolutions"][0]["delivery"]) > 0:
                print("Service delivery already exist.")
                if buisciii.utils.prompt_yn_question(
                    "Do you want to overwrite delivery info?", dflt=False
                ):
                    self.post_delivery_info()
            else:
                self.post_delivery_info()
        self.resolution_info = self.rest_api.get_request(
            request_info="service-data", safe=True, resolution=self.resolution_id
        )
        self.services_requested = self.resolution_info["resolutions"][0][
            "available_services"
        ]
        if self.type == "delivery":
            self.delivery_md_list = []
            if report_md is not None:
                if os.path.exists(report_md):
                    self.delivery_md_list.append(os.path.normpath(report_md))
                else:
                    stderr.print(
                        "[red] ERROR: Markdown file " + report_md + " does not exist."
                    )
                    sys.exit()
            else:
                self.service_ids_requested_list = (
                    buisciii.utils.append_end_to_service_id_list(
                        self.services_requested
                    )
                )
                for service_id_requested in self.service_ids_requested_list:
                    if (
                        buisciii.service_json.ServiceJson().get_find(
                            service_id_requested, "delivery_md"
                        )
                        not in self.delivery_md_list
                        and buisciii.service_json.ServiceJson().get_find(
                            service_id_requested, "delivery_md"
                        )
                        != ""
                    ):
                        self.delivery_md_list.append(
                            buisciii.service_json.ServiceJson().get_find(
                                service_id_requested, "delivery_md"
                            )
                        )

            self.results_md_list = []
            if results_md is not None:
                if os.path.exists(results_md):
                    self.results_md_list.append(os.path.normpath(results_md))
                else:
                    stderr.print(
                        "[red] ERROR: Markdown file " + results_md + " does not exist."
                    )
                    sys.exit()
            else:
                for service_id_requested in self.service_ids_requested_list:
                    if (
                        buisciii.service_json.ServiceJson().get_find(
                            service_id_requested, "results_md"
                        )
                        not in self.results_md_list
                        and buisciii.service_json.ServiceJson().get_find(
                            service_id_requested, "results_md"
                        )
                        != ""
                    ):
                        self.results_md_list.append(
                            buisciii.service_json.ServiceJson().get_find(
                                service_id_requested, "results_md"
                            )
                        )

        if self.type == "delivery":
            self.sftp_data = buisciii.utils.get_sftp_folder(conf, self.resolution_info)
        if self.type == "delivery" and sftp_folder is None:
            self.sftp_folder = self.sftp_data[0]
        else:
            self.sftp_folder = sftp_folder
        if not self.resolution_info:
            stderr.print(
                "[red] Unable to fetch information for resolution "
                + self.resolution_id
                + "!"
            )
            sys.exit(1)
        self.service_name = self.resolution_info["resolutions"][0][
            "resolution_full_number"
        ]
        self.resolution_number = self.resolution_info["resolutions"][0][
            "resolution_number"
        ]
        self.delivery_number = self.resolution_number.partition(".")[2]
        resolution_date = self.resolution_info["service_created_date"]
        self.resolution_datetime = datetime.strptime(resolution_date, "%Y-%m-%d")
        year = datetime.strftime(self.resolution_datetime, "%Y")
        self.service_folder = os.path.join(
            self.path, self.conf["services_path"], year, self.service_name
        )
        self.samples = self.resolution_info.get("samples", None)
        self.versions = self.load_versions()
        self.handled_services = None
        self.all_services = None
        try:
            self.config_pdfkit = pdfkit.configuration()
        except OSError as e:
            stderr.print(
                "[red] wkhtmlpdf executable was not found. Install it using conda environment."
            )
            stderr.print(f"[red] Error: {e}")
            sys.exit()

        if self.type == "service_info":
            self.template_file = self.conf["service_info_template_path_file"]
        else:
            self.template_file = self.conf["delivery_template_path_file"]
        self.service_info_folder = self.conf["service_folder"][0]
        self.service_result_folder = self.conf["service_folder"][1]
        if email_psswd is None and self.type == "delivery":
            stderr.print("Write password for bioinformatica@isciii.es")
            self.email_psswd = buisciii.utils.ask_password("E-mail password: ")
        else:
            self.email_psswd = email_psswd

        if self.type == "delivery":
            service_list = {}
            for service_id_requested in self.service_ids_requested_list:
                service_list[
                    service_id_requested
                ] = buisciii.service_json.ServiceJson().get_find(
                    service_id_requested, "label"
                )
            self.all_services = service_list

    def load_versions(self):
        """Load and parse the versions.yml file."""
        result = subprocess.run(
            f"find /data/ucct/bi/services_and_colaborations/*/*/{self.service_name} -name '*versions.yml'",
            stdout=subprocess.PIPE,
            text=True,
            shell=True,
        )
        versions_files = result.stdout.strip().split("\n")
        if versions_files == [""]:
            stderr.print(
                f"[red] No versions.yml files found for the service {self.service_name}!"
            )
            return "No software versions data available for this service"
        else:
            versions_data = {}
            loaded_contents = []
            for versions_file in versions_files:
                with open(versions_file, "r") as f:
                    content = yaml.safe_load(f)
                if content not in loaded_contents:
                    versions_data[versions_file] = content
                    loaded_contents.append(content)
            return versions_data

    def create_structure(self):
        if os.path.exists(self.service_folder):
            log.info("Already creted the service folder for %s", self.service_folder)
            stderr.print(
                "[green] Skiping folder creation for service "
                + self.service_folder
                + ". Trying with subfolders"
            )
            for folder in self.conf["service_folder"]:
                if os.path.exists(os.path.join(self.service_folder, folder)):
                    log.info(
                        "Already creted the service subfolders for %s",
                        self.service_folder,
                    )
                    stderr.print(
                        "[green] Skiping folder creation for service "
                        + self.service_folder
                        + "/"
                        + folder
                    )
                else:
                    log.info("Creating service subfolder %s", folder)
                    stderr.print(
                        "[blue] Creating the service subfolderfolder "
                        + folder
                        + " for "
                        + self.service_folder
                        + "!"
                    )
                    os.makedirs(
                        os.path.join(self.service_folder, folder), exist_ok=True
                    )
                    log.info("Service folders created")
                if self.type == "delivery":
                    file_path = os.path.join(
                        self.service_folder, self.service_result_folder
                    )
                    delivery_date = self.resolution_info["resolutions"][0][
                        "resolution_delivery_date"
                    ]
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
            log.info("Creating service folder for %s", self.service_folder)
            stderr.print(
                "[blue] Creating the service folder for " + self.service_folder + "!"
            )
            for folder in self.conf["service_folder"]:
                os.makedirs(os.path.join(self.service_folder, folder), exist_ok=True)
            log.info("Service folders created")
        return

    def post_delivery_info(self):
        if buisciii.utils.prompt_yn_question(
            msg="Do you wish to provide a text file for delivery notes?", dflt=False
        ):
            for i in range(3, -1, -1):
                self.provided_txt = buisciii.utils.prompt_path(
                    msg="Write the path to the file with RAW text as delivery notes"
                )
                if not os.path.isfile(os.path.expanduser(self.provided_txt)):
                    stderr.print(f"Provided file doesn't exist. Attempts left: {i}")
                else:
                    stderr.print(f"File selected: {self.provided_txt}")
                    break
            else:
                stderr.print("No more attempts. Delivery notes will be given by prompt")
                self.provided_txt = None
        else:
            self.provided_txt = None

        if self.provided_txt:
            with open(os.path.expanduser(self.provided_txt)) as f:
                self.delivery_notes = f.read()
        else:
            self.delivery_notes = buisciii.utils.ask_for_some_text(
                msg="Write some delivery notes:"
            )
        delivery_dict = {
            "resolution_number": self.resolution_id,
            "delivery_notes": self.delivery_notes,
        }

        # How json should be fully formatted:
        # delivery_dict = {
        # "resolution_number": "SRVSGAFI005.1",
        # "pipelines_in_delivery": ["viralrecon"],
        # "delivery_notes" : delivery_notes,
        # "execution_start_date" : "YYYY-MM-DD",
        # "execution_end_date" : "YYYY-MM-DD",
        # "permanent_used_space" : "",
        # "temporary_used_space" : ""
        # }

        self.rest_api.post_request("create-delivery", json.dumps(delivery_dict))
        self.rest_api.put_request(
            "update-state", "resolution", self.resolution_id, "state", "delivered"
        )

    def create_markdown(self, file_path):
        """Create the markdown fetching the information from request api"""
        log.info(
            "starting proccess to create markdown for service %s", self.service_folder
        )
        stderr.print(
            "[green] Creating service information markdown file for "
            + self.service_folder
            + " !"
        )
        log.info("Start creating the markdown file")

        markdown_data = {}
        # service related information
        markdown_data["service"] = self.resolution_info
        markdown_data["user_data"] = self.resolution_info["service_user_id"]
        markdown_data["software_versions"] = self.versions
        markdown_data["services_list"] = self.all_services
        samples_in_service = {}

        if self.samples is not None:
            for sample_data in self.samples:
                if sample_data["run_name"] not in samples_in_service:
                    samples_in_service[sample_data["run_name"]] = {}
                if (
                    sample_data["project_name"]
                    not in samples_in_service[sample_data["run_name"]]
                ):
                    samples_in_service[sample_data["run_name"]][
                        sample_data["project_name"]
                    ] = []
                samples_in_service[sample_data["run_name"]][
                    sample_data["project_name"]
                ].append(sample_data["sample_name"])
        else:
            samples_in_service = {" N/A": {" N/A": ["No recorded samples"]}}

        markdown_data["samples"] = samples_in_service

        # Resolution related information
        markdown_data["resolution"] = self.resolution_info["resolutions"][0]
        markdown_data["resolution_serviceIDs"] = []
        for available_service in self.resolution_info["resolutions"][0][
            "available_services"
        ]:
            markdown_data["resolution_serviceIDs"].append(
                available_service["avail_service_description"]
            )

        if self.type == "delivery":
            markdown_data["delivery"] = self.resolution_info["resolutions"][0][
                "delivery"
            ][0]
        f_name = self.resolution_number + "_resolution.md"
        file_name = os.path.join(file_path, f_name)

        # Delivery related information
        pakage_path = os.path.dirname(os.path.realpath(__file__))
        templateLoader = jinja2.FileSystemLoader(searchpath=pakage_path)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(self.template_file)
        # Create markdown
        mk_text = template.render(markdown_data)
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
                "nl2br",
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
            self.conf["html_template_path_file"],
        )
        css_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), self.conf["path_to_css"]
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
            stderr.print(f"[red] Error: {e}")
            log.exception("Unable to create pdf.", exc_info=e)
        return

    def generate_documentation_files(self, type):
        if type == "service_info":
            file_path = os.path.join(self.service_folder, self.service_info_folder)
        elif self.type == "delivery":
            file_path = os.path.join(
                self.service_folder,
                self.service_result_folder,
                self.delivery_sub_folder,
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

    def join_pdf_files(self, documentation_pdf, results_pdf, service_pdf):
        delivery_pdf_name = (
            self.resolution_number + "_" + self.delivery_sub_folder + ".pdf"
        )
        delivery_pdf_file = os.path.join(
            self.service_folder,
            self.service_result_folder,
            self.delivery_sub_folder,
            delivery_pdf_name,
        )
        try:
            mergeFile = PyPDF2.PdfMerger()
            mergeFile.append(PyPDF2.PdfReader(documentation_pdf, "rb"))
            if results_pdf is not None:
                mergeFile.append(PyPDF2.PdfReader(results_pdf, "rb"))
            if service_pdf is not None:
                mergeFile.append(PyPDF2.PdfReader(service_pdf, "rb"))
            mergeFile.write(delivery_pdf_file)
            stderr.print(
                "[green]Successfully merged the PDFs %s, %s and %s to the directory %s"
                % (
                    documentation_pdf,
                    results_pdf,
                    service_pdf,
                    os.path.join(
                        self.service_folder,
                        self.service_result_folder,
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

        return delivery_pdf_file

    def copy_images(self):
        file_path = os.path.join(
            self.service_folder,
            self.service_result_folder,
            self.delivery_sub_folder,
            "images",
        )
        if not os.path.exists(file_path):
            stderr.print("[green] Coping images folder temporarylly to " + file_path)
            images_folder = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "assets/reports/md/images"
            )
            shutil.copytree(images_folder, file_path, dirs_exist_ok=False)

    def create_results_doc(self, md_list, md_type):
        stderr.print(
            "[green] Creating service results markdown file for "
            + self.service_folder
            + " !"
        )
        file_path = os.path.join(
            self.service_folder,
            self.service_result_folder,
            self.delivery_sub_folder,
        )
        if md_type == "service":
            mk_text = ""
        else:
            mk_text = (
                "# Results\nHere we describe the content of the  `RESULTS` folder.\n"
            )
        for results_md in md_list:
            results_md_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), results_md
            )
            with open(results_md_path, "r") as fr:
                md_text = fr.read()
                mk_text = mk_text + "\n" + md_text

        if md_type == "service":
            mk_text = mk_text.replace(
                '<details markdown="1">', '<details open markdown="1">'
            )
            f_name = self.resolution_number + "_service.md"
        else:
            f_name = self.resolution_number + "_results.md"
        file_name = os.path.join(file_path, f_name)
        file_name_without_ext = file_name.replace(".md", "")
        html_text = self.convert_markdown_to_html(mk_text)
        html_file_name = self.wrap_html(html_text, file_name_without_ext)
        self.convert_to_pdf(html_file_name)
        pdf_file = html_file_name.replace(".html", ".pdf")
        return pdf_file

    def clean_files(self):
        file_path = os.path.join(
            self.service_folder,
            self.service_result_folder,
            self.delivery_sub_folder,
        )
        for f in os.listdir(file_path):
            if re.search("_resolution", f):
                os.remove(os.path.join(file_path, f))
            if re.search("_results", f):
                os.remove(os.path.join(file_path, f))
            if re.search("_service", f):
                os.remove(os.path.join(file_path, f))
            if re.search("images", f):
                shutil.rmtree(os.path.join(file_path, f), ignore_errors=True)

    def sftp_tree(self):
        sftp_path = os.path.join(self.sftp_folder, self.service_name)
        try:
            tree_result = subprocess.run(
                ["tree", sftp_path], capture_output=True, text=True, check=True
            )
            tree_file_name = (
                self.resolution_number + "_" + self.delivery_sub_folder + ".tree"
            )
            tree_file_path = os.path.join(
                self.service_folder,
                self.service_result_folder,
                self.delivery_sub_folder,
                tree_file_name,
            )
            f = open(tree_file_path, "w")
            f.write(tree_result.stdout)
            f.close()
            stderr.print(
                "[green]Successfully created tree file from %s in %s"
                % (sftp_path, tree_file_path),
                highlight=False,
            )

        except subprocess.CalledProcessError as e:
            stderr.print("[red]ERROR: Failed to create tree from SFTP")
            stderr.print("traceback error %s" % e)
            sys.exit()
        except IOError as e:
            stderr.print("[red]ERROR: Failed to create tree file")
            stderr.print("traceback error %s" % e)
            sys.exit()

    def email_creation(self):
        email_data = {}
        if buisciii.utils.prompt_yn_question(
            "Do you want to add some delivery notes to the e-mail?", dflt=False
        ):
            if hasattr(self, "provided_txt") and self.provided_txt is not None:
                if buisciii.utils.prompt_yn_question(
                    f"Do you want to use notes from {self.provided_txt}?", dflt=False
                ):
                    email_data["email_notes"] = self.delivery_notes.replace(
                        "\n", "<br />"
                    )
                else:
                    email_data["email_notes"] = buisciii.utils.ask_for_some_text(
                        msg="Write email notes"
                    ).replace("\n", "<br />")
            else:
                if buisciii.utils.prompt_yn_question(
                    msg="Do you wish to provide a text file for email notes?",
                    dflt=False,
                ):
                    for i in range(3, -1, -1):
                        email_data["email_notes"] = buisciii.utils.prompt_path(
                            msg="Write the path to the file with RAW text as email notes"
                        )
                        if not os.path.isfile(
                            os.path.expanduser(email_data["email_notes"])
                        ):
                            stderr.print(
                                f"Provided file doesn't exist. Attempts left: {i}"
                            )
                        else:
                            stderr.print(f"File selected: {email_data['email_notes']}")
                            break
                    else:
                        stderr.print(
                            "No more attempts. Email notes will be given by prompt"
                        )
                        email_data["email_notes"] = None
                else:
                    email_data["email_notes"] = None

                if email_data["email_notes"]:
                    with open(os.path.expanduser(email_data["email_notes"])) as f:
                        email_data["email_notes"] = f.read().replace("\n", "<br />")
                else:
                    email_data["email_notes"] = buisciii.utils.ask_for_some_text(
                        msg="Write email notes"
                    ).replace("\n", "<br />")

        email_data["user_data"] = self.resolution_info["service_user_id"]
        email_data["service_id"] = self.service_name.split("_", 5)[0]
        email_data["service_acronym"] = self.service_name.split("_", 5)[2]
        email_data["delivery_number"] = self.delivery_number
        email_data["sftp_folder"] = self.sftp_data[1]

        email_template_file = "templates/email.j2"
        pakage_path = os.path.dirname(os.path.realpath(__file__))
        templateLoader = jinja2.FileSystemLoader(searchpath=pakage_path)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(email_template_file)

        email_html = template.render(email_data)
        return email_html

    def send_email(self, html_text, results_pdf_file, attachment_files=None):
        email_host = self.conf["email_host"]
        email_port = self.conf["email_port"]
        email_host_user = self.conf["email_host_user"]
        email_host_password = self.email_psswd
        email_use_tls = self.conf["email_use_tls"]

        context = ssl.create_default_context()
        try:
            server = SMTP(host=email_host, port=email_port)
            server.ehlo()
            if email_use_tls:
                server.starttls(context=context)
            server.ehlo()
            server.login(user=email_host_user, password=email_host_password)
        except Exception as e:
            stderr.print("[red] Unable to send e-mail: " + str(e))
        default_cc = "bioinformatica@isciii.es"
        msg = MIMEMultipart("alternative")
        msg["To"] = self.resolution_info["service_user_id"]["email"]
        msg["From"] = email_host_user
        msg["Subject"] = (
            "Entrega "
            + self.delivery_number
            + " - "
            + self.service_name.split("_", 5)[0]
            + " - "
            + self.service_name.split("_", 5)[2]
        )
        if buisciii.utils.prompt_yn_question(
            "Do you want to add any other sender? apart from %s. Note: %s is the default CC."
            % (self.resolution_info["service_user_id"]["email"], default_cc),
            dflt=False,
        ):
            stderr.print(
                "[red] Write emails to be added in semicolon separated format: icuesta@isciii.es;user2@isciii.es"
            )
            cc_address = buisciii.utils.ask_for_some_text(msg="E-mails:")
        else:
            cc_address = str()
        if cc_address:
            msg["CC"] = str(default_cc + ";" + str(cc_address))
        else:
            msg["CC"] = default_cc
        rcpt = msg["CC"].split(";") + [msg["To"]]
        html = MIMEText(html_text, "html")
        msg.attach(html)
        with open(results_pdf_file, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header(
            "Content-Disposition",
            "attachment",
            filename=str(os.path.basename(results_pdf_file)),
        )
        msg.attach(attach)

        if buisciii.utils.prompt_yn_question(
            "Do you want to attach additional files?", dflt=False
        ):
            stderr.print("[cyan] Provide additional files separated by semicolons (;)")
            extra_files_input = buisciii.utils.ask_for_some_text(
                msg="Attachment paths:"
            )
            attachment_files = [
                os.path.expanduser(p.strip())
                for p in extra_files_input.split(";")
                if p.strip()
            ]

            for file_path in attachment_files:
                if file_path and os.path.isfile(file_path):
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), _subtype="octet-stream")
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(file_path),
                    )
                    msg.attach(part)
                else:
                    stderr.print(
                        f"[yellow] Attachment not found or invalid: {file_path}"
                    )

        server.sendmail(
            email_host_user,
            rcpt,
            msg.as_string(),
        )
        server.quit()
        stderr.print("[green] Mail sent correctly")

    def create_documentation(self):
        self.create_structure()
        if self.type == "service_info":
            self.generate_documentation_files("service_info")
            return
        elif self.type == "delivery":
            doc_pdf = self.generate_documentation_files("delivery")
            self.copy_images()
            if self.results_md_list:
                result_pdf = self.create_results_doc(self.results_md_list, "results")
            else:
                stderr.print("Results markdown does not exist.")
                if buisciii.utils.prompt_yn_question(
                    "Do you want to continue without it?", dflt=True
                ):
                    result_pdf = None
                else:
                    stderr.print("Bye.")
                    sys.exit(1)
            if self.delivery_md_list:
                service_pdf = self.create_results_doc(self.delivery_md_list, "service")
            else:
                stderr.print("Delivery markdown does not exist.")
                if buisciii.utils.prompt_yn_question(
                    "Do you want to continue without it?", dflt=True
                ):
                    service_pdf = None
                else:
                    stderr.print("Bye.")
                    sys.exit(1)
            results_pdf = self.join_pdf_files(doc_pdf, result_pdf, service_pdf)
            self.clean_files()
            self.sftp_tree()
            email_html = self.email_creation()
            if buisciii.utils.prompt_yn_question(
                "Do you want to send e-mail automatically?", dflt=True
            ):
                self.send_email(email_html, results_pdf)
            else:
                print(email_html)
            return
        else:
            stderr.print("[red] invalid option")
            log.error("Unable to proceed because invalid option %s", type)
            sys.exit(1)
