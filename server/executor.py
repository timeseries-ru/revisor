import importlib
import traceback
import inspect
import os

import revisor as rv
from serializer import Serializer

import pandas as pd

def bump_version(data):
    path = Serializer().get_folder_name(data['project'])
    project = Serializer().read_project(path)
    project['predictions_model'] = data['version']
    return Serializer().save_project(path, project)

def bump_settings(data):
    path = Serializer().get_folder_name(data['project'])
    return Serializer().update_settings(path, data['version'], data['settings'])

def get_estimator(path, json, version=None):
    sandbox = dict()
    for short_name, module in json['model']['imports']:
        sandbox[short_name] = importlib.import_module(module)
    exec(json['implementation'], sandbox)
    version = version if version is not None else json['version']
    if version is None:
        version = Serializer().read_project(path)['predictions_model']
    model = rv.Model(json['model']['name'])
    model.server_path = os.path.join(
        path, 'model_' + str(version) + '.data'
    )
    model.settings = json['model']['settings']
    data_path = Serializer().actual_dataset_file(path, version)
    if data_path:
        model.set_dataset(pd.read_pickle(data_path, compression='bz2'))
    estimator = (sandbox[json['class_name']])()
    if callable(estimator):
        estimator = estimator()
    return estimator, model, version

def fit_implementation(project_name, version, registry_add):

    path = Serializer().get_folder_name(project_name)
    json = Serializer().read_model(path, version)

    if not 'error' in json:
        estimator, model, version = get_estimator(path, json, version)
        messages = []
        try:
            producer = estimator.fit(model)
            if inspect.isgenerator(producer):
                for message in producer:
                    messages.append(message)
            else:
                messages = producer
            Serializer().save_changes(path, version, model, add=False)
            Serializer().save_fit_logs(path, version, messages)
            if model.get_dashboard():
                Serializer().set_dashboard(
                    path, model.get_dashboard()
                )
        except:
            return {'exception': traceback.format_exc()}
        if model.registered_instance is not None:
            registry_add(
                project_name, model, model.registered_instance
            )
        return messages if messages is not None else {}
    return {'error': True}

def implementation_predict(project_name, values, version):
    path = Serializer().get_folder_name(project_name)
    json = Serializer().read_model(path, version)

    if not 'error' in json:
        estimator, model, version = get_estimator(path, json, version)
        try:
            result = estimator.predict(model, values)
            Serializer().save_changes(path, version, model, add=True)
            if model.get_dashboard():
                Serializer().set_dashboard(
                    path, model.get_dashboard()
                )
        except:
            return {'exception': traceback.format_exc()}
        return result
    return {'error': True}

def implementation_tasks():
    projects = Serializer().list_projects()
    for project in projects:
        if not 'schedule' in project['project']:
            continue
        if not project['project']['schedule']:
            continue
        version = project['project']['predictions_model']
        path = Serializer().get_folder_name(project['project']['name'])
        json = Serializer().read_model(path, version)
        if not 'error' in json:
            estimator, model, version = get_estimator(path, json, version)
            try:
                if hasattr(estimator, 'task'):
                    if callable(estimator.task):
                        result = estimator.task(model)
                        Serializer().save_changes(
                            path, version, model, add=False
                        )
                        if model.get_dashboard():
                            Serializer().set_dashboard(
                                path, model.get_dashboard()
                            )
            except:
                Serializer().log_error()
