import os
import json
import re

from glob import glob
import datetime as dt
import traceback

from hashlib import blake2s
def hashing(string):
    value = blake2s(digest_size=20)
    value.update(string.encode())
    return value.hexdigest()

class Serializer():

    def get_folder_name(self, project_name):
        return os.path.join('saved_models', hashing(project_name))

    def log_error(self):
        with open('logs.txt', 'a') as logsfile:
            logsfile.write(
                str(dt.datetime.now()) + " " + traceback.format_exc()
            )

    def read_project(self, folder):
        project = {'error': True}
        try:
            with open(os.path.join(folder, 'project.json'), 'r') as jsonfile:
                project = json.load(jsonfile)
        except:
            self.log_error()
        return project

    def save_project(self, path, project_data):
        try:
            with open(os.path.join(path, 'project.json'), 'w') as jsonfile:
                project = json.dump(project_data, jsonfile)
        except:
            self.log_error()
            return {'error': True}
        return {'ok': True}

    def read_model(self, folder, version):
        if (version is None) or (not os.path.exists(
            os.path.join(folder, 'model_' + str(version) + '.json')
        )):
            return self.read_predictions_model(folder)
        else:
            model = {'error': True, 'message': 'Model not found'}
            try:
                with open(
                    os.path.join(folder, 'model_' + str(version) + '.json'), 'r'
                ) as jsonfile:
                    model = json.load(jsonfile)
            except:
                self.log_error()
            return model

    def read_predictions_model(self, folder):
        model = {'error': True}
        project = self.read_project(folder)
        try:
            current = 'model_' + str(project['predictions_model']) + '.json'
            with open(
                os.path.join(folder, current), 'r'
            ) as jsonfile:
                model = json.load(jsonfile)
        except:
            self.log_error()
        return model

    def actual_dataset_file(self, folder, version):
        try:
            project = self.read_project(folder)
            if version is None:
                version = project['predictions_model']
            models_data = sorted(
                glob(os.path.join(folder, 'model_*.data'))
            )
            if not os.path.exists(os.path.join(os.path.join(
                folder, 'model_' + str(version) + '.data'
            ), 'dataset.bz2')):
                for index in reversed(range(1, int(version))):
                    current = os.path.join(os.path.join(
                        folder, 'model_' + str(index) + '.data'
                    ), 'dataset.bz2')
                    if os.path.exists(current):
                        return current
            else:
                return os.path.join(os.path.join(
                    folder, 'model_' + str(version) + '.data'
                ), 'dataset.bz2')
        except:
            self.log_error()

    def list_projects(self):
        projects = []
        for folder_data in os.listdir('saved_models'):
            folder_data = os.path.join('saved_models', folder_data)
            if os.path.isfile(folder_data):
                continue
            if folder_data != 'saved_models':
                projects.append({
                    'project': self.read_project(folder_data),
                    'predictions_model': self.read_predictions_model(folder_data)
                })
        return projects

    def list_models(self, project_name):
        try:
            for folder_data in os.listdir('saved_models'):
                folder_data = os.path.join('saved_models', folder_data)
                if os.path.isfile(folder_data):
                    continue
                if folder_data == os.path.join(
                    'saved_models', str(hashing(project_name))
                ):
                    models_jsons = sorted(
                        glob(os.path.join(folder_data, 'model_*.json'))
                    )
                    models = []
                    for jsonfile in models_jsons:
                        with open(jsonfile, 'r') as current:
                            models.append(json.load(current))
                    models = {
                        'models': models,
                        'project': self.read_project(folder_data)
                    }
                    return models
        except:
            self.log_error()
        return {'error': True}

    def save_visualizations(self, path, version, model):
        current = self.read_model(path, version)
        for description, visualization in model.visualizations:
            current['model']['visualizations'].append(
                (description, visualization)
            )
        with open(
            os.path.join(path, 'model_' + str(version) + '.json'), 'w'
        ) as fd:
            json.dump(current, fd)

    def save_fit_logs(self, path, version, messages):
        current = self.read_model(path, version)
        current['model']['messages'] = messages
        with open(
            os.path.join(path, 'model_' + str(version) + '.json'), 'w'
        ) as fd:
            json.dump(current, fd)

    def update_settings(self, path, version, settings):
        current = self.read_model(path, version)
        current['model']['settings'] = settings
        current['model']['changed'] = True
        with open(
            os.path.join(path, 'model_' + str(version) + '.json'), 'w'
        ) as fd:
            json.dump(current, fd)
        return {'ok': True}

    def set_dashboard(self, path, image):
        project = self.read_project(path)
        project['dashboard'] = image
        if (image is not None) and (len(image) > 0):
            project['dashboard_url'] = hashing(project['name'])
        else:
            project['dashboard_url'] = None
        with open(os.path.join(path, 'project.json'), 'w') as fd:
            json.dump(project, fd)

    def save_model(self, request_body, datafile, with_rewrite=False):
        try:
            folder_path = os.path.join(
                'saved_models', str(hashing(request_body['project']))
            )
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                predictions_model = 1
            else:
                predictions_model = self.read_project(folder_path)[
                    'predictions_model'
                ]
            with open(
                os.path.join(folder_path, 'project.json'), 'w'
            ) as jsonfile:
                jsonfile.write(json.dumps({
                    'name': request_body['project'],
                    'description': request_body['description'],
                    'predictions_model': predictions_model
                }))
            models_jsons = sorted(
                glob(os.path.join(folder_path, 'model_*.json'))
            )
            latest = 1
            if len(models_jsons) > 0:
                last = os.path.basename(list(models_jsons)[-1])
                latest = int(
                    re.search('([0-9]+)', last).group(0)
                ) + (0 if with_rewrite else 1)
            with open(
                os.path.join(folder_path, 'model_' + str(latest) + '.json'), 'w'
            ) as jsonfile:
                request_body['model']['deploy_time'] = str(dt.datetime.now())
                jsonfile.write(json.dumps({
                    'implementation': request_body['implementation'],
                    'class_name': request_body['class_name'],
                    'has_dataset': request_body['has_dataset'],
                    'model': request_body['model'],
                    'version': latest
                }))
            if datafile is not None:
                data_path = os.path.join(
                    folder_path, 'model_' + str(latest) + '.data'
                )
                if not os.path.exists(data_path):
                    os.makedirs(data_path)
                with open(
                    os.path.join(data_path, 'dataset.bz2'), 'wb'
                ) as binary:
                    binary.write(datafile.file.read())
        except:
            self.log_error()
            return {'error': True}
        return {'ok': True}
