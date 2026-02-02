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
            Get the dictionary JSON data.
        """
        return self.json_data

    def get_service_list(self):
        """
        Description:
            Get the service list.
        """
        return self.service_list

    def get_service_configuration(self, service):
        """
        Description:
            Obtain the service configuration from JSON data.
        """
        if service in self.service_list:
            return self.json_data[service]
        return None

    def get_find(self, service, found):
        """
        Description:
            Obtain from service any forward items from JSON data.
        """
        if found in self.json_data[service]:
            return self.json_data[service][found]
        else:
            for key, value in self.json_data[service].items():
                if isinstance(value, dict):
                    if found in self.json_data[service][key]:
                        return self.json_data[service][key][found]
            return None

    def get_find_aux(self, service, found):
        """
        Description:
            Recursively search for a key in a nested dictionary or list.
        """
        if isinstance(service, dict):
            if found in service:
                return service[found]
            for key in service:
                finder = self.get_find_aux(service[key], found)
                if finder is not None:
                    return finder
        if isinstance(service, list):
            for object in service:
                finder = self.get_find_aux(object, found)
                if finder is not None:
                    return finder
        return None

    def get_find_deep(self, service, found):
        """
        Description:
            Perform a deep search for a key.
        """
        if service in self.service_list:
            serv_dict = self.json_data[service]
            call_aux = self.get_find_aux(serv_dict, found)
            return call_aux
        else:
            return "service not found"

    def my_recursivity(self, service, found_item):
        """
        Description:
            Recursively search for a key in the service's JSON configuration.
        """

        def recursive(my_dict, found_item):
            if isinstance(my_dict, dict):
                for key, values in my_dict.items():
                    if key == found_item:
                        return values
                    if isinstance(values, dict):
                        data = recursive(values, found_item)
                        if data:
                            return data
                return False

        if service in self.service_list:
            return recursive(self.json_data[service], found_item)
        return False

    def get_list_of_delivery_doc(self):
        """
        Description:
            Return a dictionary mapping each service to its corresponding delivery PDF file.
        """
        docs = {}
        for service in self.service_list:
            docs[service] = self.json_data[service]["delivery_pdf"]
        return docs
