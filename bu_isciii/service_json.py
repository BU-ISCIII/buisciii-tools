#!/usr/bin/env python
import json


class ServiceJson:
    def __init__(self, json_file=os.path.join(os.path.dirname(__file__), "templates")):
        fh = open(json_file)
        self.json_data = json.load(fh)
        fh.close()
        self.service_list = list(self.json_data.keys())

    def get_service_list(self):
        return self.service_list

    def get_service_configuration(self, service):
        if service in self.service_list:
            return self.json_data[service]
        return None
