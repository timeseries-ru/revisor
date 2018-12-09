import inspect
import requests
import json
import tempfile
import os

import pandas as pd

class Project():
    def __init__(self, project_name, server_path='http://localhost:8000'):
        self.server_path = server_path
        self.project_name = project_name
        self.description = ''

    def set_description(self, description):
        self.description = description

    def fit(self, token, version=None):
        proxies = self.get_proxies()
        return requests.post(
            self.server_path + '/projects/' + self.project_name +'/fit/' + (
                '' if version is None else str(version)
            ), cookies={'token': token}, proxies=proxies
        ).json()

    def predict(self, X, token, version=None):
        proxies = self.get_proxies()
        return requests.post(
            self.server_path + '/projects/' + self.project_name + '/predict/' +
            (
                '' if version is None else str(version)
            ), cookies={'token': token}, proxies=proxies,
            json=X
        ).json()

    def get_proxies(self):
        proxies = {
            'http': None,
            'https': None
        }
        if 'http_proxy' in os.environ:
            proxies['http'] = os.environ['http_proxy']
        if 'https_proxy' in os.environ:
            proxies['https'] = os.environ['https_proxy']
        return proxies

    def set_predictions_version(self, token, version):
        proxies = self.get_proxies()
        data = requests.post(self.server_path + '/projects/update', json={
            'project': self.project_name,
            'version': version
        }, cookies={'token': token}, proxies=proxies)
        if data.status_code != 200:
            return {'error': str(data.status_code)}
        return data.json()

    def deploy(self, model, implementation, token, with_rewrite=False):
        dumped_code = inspect.getsource(implementation)
        files = {'': None}
        if model.get_dataset() is not None:
            fd = tempfile.NamedTemporaryFile(
                mode='wb', delete=False, suffix='.bz2'
            )
            filename = fd.name
            fd.close()
            model.get_dataset().to_pickle(filename, compression='bz2')
            files = {'dataset': open(filename, 'rb')}
        proxies = self.get_proxies()
        data = requests.post(self.server_path + '/projects', data={
            'data': json.dumps({
                'project': self.project_name,
                'description': self.description,
                'implementation': dumped_code,
                'class_name': implementation.__name__,
                'has_dataset': model.get_dataset() is not None,
                'model': {
                    'name': model.name,
                    'settings': model.settings,
                    'visualizations': model.visualizations,
                    'imports': model.imports
                },
                'rewrite': with_rewrite
            })
        }, cookies={'token': token}, files=files, proxies=proxies)
        if model.get_dataset() is not None:
            try:
                files['dataset'].close()
                os.unlink(filename)
            except:
                pass # exactly!
        if data.status_code != 200:
            return {'error': str(data.status_code)}
        return data.json()
