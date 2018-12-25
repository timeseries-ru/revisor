import os
import io

import xml.etree.cElementTree as etree
import pandas as pd

def is_svg(source):
    tag = None
    try:
        tag = etree.fromstring(source).tag
    except etree.ParseError:
        pass
    return tag == '{http://www.w3.org/2000/svg}svg'

class Model():
    def __init__(self, name):
        self.name = name
        self.settings = []
        self.visualizations = []
        self.dataset = None
        self.server_path = None
        self.registered_instance = None
        self.dashboard = None
        self.imports = []

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def add_import(self, short_name, module):
        self.imports.append((short_name, module))

    def add_setting(self, setting_name, setting_type, setting_value=None):
        self.settings.append((setting_name, setting_type, setting_value))

    def set_setting(self, setting_name, setting_value):
        for index, setting in enumerate(self.settings):
            if setting[0] == setting_name:
                self.settings[index] = (setting[0], setting[1], setting_value)
                return
        raise ValueError('Setting ' + setting_name + ' not found')

    def get_setting_type(self, name):
        for setting in self.settings:
            if setting[0] == name:
                return setting[1]

    def get_setting_value(self, name):
        for setting in self.settings:
            if setting[0] == name:
                return setting[2]

    def add_visualization(self, image, description = ""):
        if self.server_path is None:
            raise Exception('Not on server')
        if not is_svg(image):
            raise ValueError('Attached image is not is SVG format')
        self.visualizations.append((description, image))

    def add_visualization_figure(self, figure, description = ""):
        if self.server_path is None:
            raise Exception('Not on server')
        image = io.StringIO()
        figure.savefig(image, format='svg')
        image.seek(0)
        self.visualizations.append((description, image.getvalue()))
        image.close()

    def get_visualizations(self):
        return self.visualizations

    def set_dashboard(self, image):
        if self.server_path is None:
            raise Exception('Not on server')
        if not is_svg(image):
            raise ValueError('Attached image is not is SVG format')
        self.dashboard = image

    def set_dashboard_html(self, html):
        if self.server_path is None:
            raise Exception('Not on server')
        self.dashboard = html

    def set_dashboard_figure(self, figure):
        if self.server_path is None:
            raise Exception('Not on server')
        image = io.StringIO()
        figure.savefig(image, format='svg')
        image.seek(0)
        self.dashboard = image.getvalue()
        image.close()

    def set_dashboard_report(self, markdown, styles=""):
        if self.server_path is None:
            raise Exception('Not on server')
        self.dashboard = (markdown, styles)

    def get_dashboard(self):
        return self.dashboard

    def set_dataset(self, dataset):
        if dataset is None:
            self.dataset = None
        else:
            if not isinstance(dataset, pd.DataFrame):
                raise ValueError('Dataset must be pandas DataFrame')
            self.dataset = dataset

    def get_dataset(self):
        return self.dataset

    def on_server(self):
        return self.server_path is not None

    def open_file_on_server(self, name, mode):
        if self.server_path is None:
            raise Exception('Not on server')
        return open(os.path.join(self.server_path, name), mode)

    def register_instance_on_server(self, instance):
        if self.server_path is None:
            raise Exception('Not on server')
        self.registered_instance = instance
