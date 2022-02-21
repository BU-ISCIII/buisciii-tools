#!/usr/bin/env python
'''
=============================================================
HEADER
=============================================================
INSTITUTION: BU-ISCIII
AUTHOR: Sara Monzon; Sarai Varona
MAIL: smonzon@isciii.es; s.varona@isciii.es
CREATED: 21-02-2022
DESCRIPTION:
OPTIONS:

USAGE:

REQUIREMENTS:

TO DO:
    -INIT: where to find the needed values
    -PATH: where to be placed
        -BASE_DIRECTORY: where is it? How do we know where it is?


    -NAMING: let's be honest, those are terrible
================================================================
END_OF_HEADER
================================================================
'''
# Generic imports
import sys
import os

# Local imports

class NewService(self):
    def __init__(self,resolution_id,service_folder,service_label,service_id):
        self.resolution_id = resolution_id
        self.service_folder = service_folder
        self.service_label = service_label
        self.service_id = service_id

    def create_folder(self):
        return True

    def copy_template(self):
        return True

    def get_resolution_id(self):
        return self.resolution_id

    def get_service_folder(self):
        return self.service_folder

    def get_service_label(self):
        return self.service_label

    def get_service_id(self):
        return self.get_service_id
