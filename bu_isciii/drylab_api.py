#!/usr/bin/env python
import requests
import json


class RestServiceApi:
    def __init__(self, server, url):
        self.request_url = server + url
        self.headers = {
            "content-type": "application/json",
        }

    def get_request(self, request_info, parameter, value):
        url_http = str(self.request_url + request_info + "?" + parameter + "=" + value)
        try:
            r = requests.get(url_http, headers=self.headers)
            return json.loads(r.text)
        except:
            return False

    def put_request(self, request_info, parameter, value):
        url_http = str(self.request_url + request_info + "?" + parameter + "=" + value)
        try:
            r = requests.get(url_http, headers=self.headers)
            return True
        except:
            return False


""" Example usage
    rest_api = RestServiceApi('http://localhost:8000/', 'drylab/api/')
    services_queue = rest_api.get_request('services/','state','queued')
"""
""" Example request for iSkyLIMS
    Request:    'drylab/api/services?state=<servicese_state>'
    Method:     get
    Description:    return all services defined on iSkyLIMS which have the state
            defined in the requested with the following information:
                'pk', 'serviceRequestNumber','serviceStatus', 'serviceUserId',
                'serviceCreatedOnDate', 'serviceSeqCenter', 'serviceAvailableService',
                'serviceFileExt' , 'serviceNotes

    Request:    'drylab/api/resolution?state=<resolution_state>'
    Method:     get
    Description:    return all resolutions defined on iSkyLIMS which have the state
            defined in the requested with the following information:
                'pk','resolutionNumber', 'resolutionFullNumber','resolutionServiceID',
                'resolutionDate', 'resolutionEstimatedDate', 'resolutionOnQueuedDate' ,
                'resolutionOnInProgressDate' , 'resolutionDeliveryDate' ,
                'resolutionNotes', 'resolutionPipelines'

    Request:    'drylab/api/serviceFullData?service=<service_nuber>'
    Method:     get
    Description:    return the Samples, resolutions, and the information requested
            when creating the service with the following information:
            Related to service:
                'pk', 'serviceRequestNumber','serviceStatus', 'serviceUserId',
                'serviceCreatedOnDate', 'serviceSeqCenter', 'serviceAvailableService',
                'serviceFileExt' , 'serviceNotes
            Related to Resolutions:
                'pk','resolutionNumber', 'resolutionFullNumber','resolutionServiceID',
                'resolutionDate', 'resolutionEstimatedDate', 'resolutionOnQueuedDate' ,
                'resolutionOnInProgressDate' , 'resolutionDeliveryDate' ,
                'resolutionNotes', 'resolutionPipelines'
            Related to Samples:
                'runName', 'projectName', 'sampleName' , 'samplePath'


    Request:    'drylab/api/samplesInService?service=<service_number>'
    Method:     get
    Description:    Return the <run name> , <project name>, <sample name> and
            <sample path> for all samples requested in the service
                'runName', 'projectName', 'sampleName' , 'samplePath'


    Request:    'drylab/api/update?resolution=<resolution_state>
    Method:     put
    Description:


    Request:    'drylab/api/delivery
    Method:     post
    Description:




"""
