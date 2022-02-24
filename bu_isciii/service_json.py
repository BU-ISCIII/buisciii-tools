#!/usr/bin/env python
import json
import os


class ServiceJson:
    def __init__(
        self,
        json_file=os.path.join(os.path.dirname(__file__), "templates", "services.json"),
    ):
        fh = open(json_file)
        self.json_data = json.load(fh)
        fh.close()
        self.service_list = list(self.json_data.keys())

    def get_json_data(self):
        """
        Description:
            Get the dictionary json data
        """
        return self.json_data

    def get_service_list(self):
        """
        Description:
            Get the servicie list
        """
        return self.service_list

    def get_service_configuration(self, service):
        """
        Description:
            Obtain the service configuration from json data
        """
        if service in self.service_list:
            return self.json_data[service]
        return None

    def get_find(self, service, found):
        """
        Owner: Pablo
        Description:
            Obtain from servicie any forward items from json data
        """
        if found in self.json_data[service]:
            return self.json_data[service][found]
        else:
            for key, value in self.json_data[service].items():
                if isinstance(value, dict):
                    if found in self.json_data[service][key]:
                        return self.json_data[service][key][found]
            return None
