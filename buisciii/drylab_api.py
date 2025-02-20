#!/usr/bin/env python
import logging
import json
import requests
import sys
import rich
import buisciii.utils

log = logging.getLogger(__name__)
stderr = rich.console.Console(
    stderr=True,
    style="dim",
    highlight=False,
    force_terminal=buisciii.utils.rich_force_colors(),
)


class RestServiceApi:
    def __init__(self, server, url, user, password):
        self.request_url = server + url
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        if not user:
            stderr.print("[red]Missing user for api request")
            buisciii.utils.ask_for_some_text("API user: ")
        if not password:
            stderr.print("[red]Missing password for api request")
            buisciii.utils.ask_password("User password: ")
        else:
            self.auth = (user, password)

    # TODO: this is waaay too dirty, find a way to pass variable number of parameters and values.
    # by Guille: I used an f-string instead of all the + stuff, I think thats cleaner?
    # by Guille: **kwargs time!
    def get_request(self, request_info, safe=True, **kwargs):
        url_http = f"{self.request_url}{request_info}?{''.join([f'{key}={value}&' for key,value in kwargs.items()])[:-1]}"
        try:
            req = requests.get(url_http, headers=self.headers)
            if req.status_code > 201:
                if safe:
                    resolution = kwargs.get("resolution", "unknown")
                    log.info(
                        f"Resolution {resolution} does not exist. Status code: {req.status_code}"
                    )
                    stderr.print(
                        f"Resolution {resolution} does not exist! Please make sure the resolution ID is correct and has been created"
                    )
                    sys.exit(1)
                else:
                    return req.status_code
            return json.loads(req.text)
        except requests.ConnectionError:
            log.error("Unable to open connection towards iSkyLIMS, aborting")
            sys.exit(1)
            return False

    def put_request(
        self, request_info, parameter1, value1, parameter2, value2, safe=True
    ):
        url_http = str(
            self.request_url
            + request_info
            + "?"
            + parameter1
            + "="
            + value1
            + "&"
            + parameter2
            + "="
            + value2
        )
        try:
            req = requests.put(url_http, headers=self.headers, auth=self.auth)
            if req.status_code > 201:
                if safe:
                    log.error(
                        "Resolution id does not exist. Status code: "
                        + str(req.status_code)
                    )
                    sys.exit(1)
                else:
                    return req.status_code
            # return json.loads(req.text)
            return True
        except requests.ConnectionError:
            log.error("Unable to open connection towards iSkyLIMS")
            sys.exit(1)
            return False

    def post_request(self, request_info, data, safe=True):
        url_http = self.request_url + request_info
        try:
            req = requests.post(
                url_http, data=data, headers=self.headers, auth=self.auth
            )
            if req.status_code > 201:
                if safe:
                    log.error(
                        "Some error occurred. Status code: " + str(req.status_code)
                    )
                    log.error("Status text: " + str(json.loads(req.text)))
                    sys.exit()
                else:
                    return req.status_code
            return True

        except requests.ConnectionError:
            log.error("Unable to open connection towards iSkyLIMS, aborting")
            sys.exit(1)
            return False


""" def basic_authentication(self):
        # Pseudo-code for credentials validation, returns error 404 right now
        from requests.auth import HTTPBasicAuth

        user, password = self.auth[0], self.auth[1]
        url_http = self.request_url
        response = requests.get(url_http, auth=HTTPBasicAuth(user, password))
        print("Response status code", response.status_code)
        if response.status_code <= 200:
            return True
        else:
            return False
"""

""" Example usage
    rest_api = RestServiceApi("http://localhost:8000/", "drylab/api/")
    services_queue = rest_api.get_request("service/", "state", "queued")
    update_resolution = rest_api.put_request(resolution, "finish")
"""
""" Example request for iSkyLIMS
    Request:    "drylab/api/services?state=<servicese_state>"
    Method:     get
    Description:   return all services defined on iSkyLIMS which have the state
        defined in the requested with the following information:
           "pk", "serviceRequestNumber","serviceStatus", "serviceUserId",
            "serviceCreatedOnDate", "serviceSeqCenter", "serviceAvailableService",
            "serviceFileExt", "serviceNotes

    Request:    "drylab/api/resolution?state=<resolution_state>"
    Method:     get
    Description: return all resolutions defined on iSkyLIMS which have the
        state defined in the requested with the following information:
            "pk", "resolutionNumber", "resolutionFullNumber",
            "resolutionServiceID", "resolutionDate", "resolutionEstimatedDate",
            "resolutionOnQueuedDate", "resolutionOnInProgressDate",
            "resolutionDeliveryDate", "resolutionNotes", "resolutionPipelines"

    Request:    "drylab/api/serviceFullData?service=<service_nuber>"
    Method:     get
    Description:    return the Samples, resolutions, and the information requested
            when creating the service with the following information:
            Related to service:
                "pk", "serviceRequestNumber", "serviceStatus", "serviceUserId",
                "serviceCreatedOnDate", "serviceSeqCenter", "serviceAvailableService",
                "serviceFileExt", "serviceNotes"
            Related to Resolutions:
                "pk","resolutionNumber", "resolutionFullNumber", "resolutionServiceID",
                "resolutionDate", "resolutionEstimatedDate", "resolutionOnQueuedDate",
                "resolutionOnInProgressDate", "resolutionDeliveryDate",
                "resolutionNotes", "resolutionPipelines"
            Related to Samples:
                "runName", "projectName", "sampleName", "samplePath"


    Request:    "drylab/api/samplesInService?service=<service_number>"
    Method:     get
    Description:    Return the <run name> , <project name>, <sample name> and
            <sample path> for all samples requested in the service
                "runName", "projectName", "sampleName", "samplePath"


    Request:    "drylab/api/update?resolution=<resolution_state>
    Method:     put
    Description:


    Request:    "drylab/api/delivery
    Method:     post
    Description:
"""
