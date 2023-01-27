#!/usr/bin/env python
import logging
import json
import requests
import sys

log = logging.getLogger(__name__)


class RestServiceApi:
    def __init__(self, server, url):
        self.request_url = server + url
        self.headers = {"content-type": "application/json"}

    # TODO: this is waaay too dirty, find a way to pass variable number of parameters and values.
    def get_request(
        self, request_info, parameter1, value1, parameter2=None, value2=None, safe=True
    ):
        if parameter2 is None:
            url_http = str(
                self.request_url + request_info + "?" + parameter1 + "=" + value1
            )
        else:
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
            req = requests.get(url_http, headers=self.headers)
            if req.status_code > 201:
                if safe:
                    log.error(
                        "Resolution id does not exist. Status code: "
                        + str(req.status_code)
                    )
                    sys.exit()
                else:
                    return req.status_code
            return json.loads(req.text)
        except requests.ConnectionError:
            log.error("Unable to open connection towards iSkyLIMS")
            return False

    def put_request(self, request_info, parameter1, value1, parameter2, value2, safe=True):
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
        #url_http = str(self.request_url + request_info + "?" + parameter + "=" + value)
        try:
            req = requests.put(url_http, headers=self.headers)
            if req.status_code > 201:
                if safe:
                    log.error(
                        "Resolution id does not exist. Status code: "
                        + str(req.status_code)
                    )
                    sys.exit()
                else:
                    return req.status_code
            #return json.loads(req.text)
            return True
        except requests.ConnectionError:
            log.error("Unable to open connection towards iSkyLIMS")
            return False

    def post_request(self, data):
        try:
            req = requests.post(self.request_url, data=data, headers=self.headers)
            if req.status_code > 201:
                log.error(str(req.status_code))
                return False
        except requests.ConnectionError:
            log.error("Unable to open connection towards iSkyLIMS")
        return True


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
