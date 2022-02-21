#!/usr/bin/env python
import requests
import json

class RestServiceApi:
    def __init__(self, server, url):
        self.request_url = server + url
        self.headers = {"content-type": "application/json",}


    def get_request(self, request_info, parameter, value):
        url_http = str(self.request_url + request_info +'?'+ parameter + '=' + value)
        try:
            r = requests.get(url_http,  headers=self.headers)
            return json.loads(r.text)
        except:
            return False

    def put_request(self, request_info,parameter, value):
        url_http = str(self.request_url + request_info +'?'+ parameter + '=' + value)
        try:
            r = requests.get(url_http,  headers=self.headers)
            return True
        except:
            return False

''' Example usage
    rest_api = RestServiceApi('http://localhost:8000/', 'drylab/api/')
    services_queue = rest_api.get_request('services/','state','queued')
'''
