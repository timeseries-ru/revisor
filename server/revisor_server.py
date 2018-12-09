import falcon
import json
import os

from serializer import Serializer, hashing
from falcon_multipart.middleware import MultipartMiddleware

from executor import fit_implementation, implementation_predict,\
                     bump_version, bump_settings

from users import PROJECTS_USERS

def check_token(request):
    if not 'token' in request.cookies:
        return False
    token = request.cookies['token']
    for user in PROJECTS_USERS:
        if hashing(PROJECTS_USERS[user]) == token:
            return True
    return False

class LoginResource:
    def on_post(self, request, response):
        data = json.loads(request.stream.read())
        if 'name' in data:
            if data['name'] in PROJECTS_USERS:
                user = data['name']
                if hashing(PROJECTS_USERS[user]) == hashing(data['pass']):
                    response.media = {
                        'ok': True,
                        'token': hashing(data['pass'])
                    }
                    return
        response.media = {'error': True}

class ProjectResource:
    def on_get(self, request, response):
        if not check_token(request):
            response.media = {'error': True, 'message': 'Not authorized'}
            return
        response.media = Serializer().list_projects()

    def on_post(self, request, response):
        if not check_token(request):
            response.media = {'error': True, 'message': 'Not authorized'}
            return
        body = json.loads(request.get_param('data'))
        data = request.get_param('dataset')
        response.media = Serializer().save_model(
            body, data, body['rewrite']
        )

class VersionResource:
    def on_post(self, request, response):
        if not check_token(request):
            response.media = {'error': True, 'message': 'Not authorized'}
            return
        response.media = bump_version(
            json.loads(request.stream.read().decode())
        )

class SettingsResource:
    def on_post(self, request, response):
        if not check_token(request):
            response.media = {'error': True, 'message': 'Not authorized'}
            return
        response.media = bump_settings(
            json.loads(request.stream.read().decode())
        )

class ModelsResource:
    def on_get(self, request, response, name):
        if not check_token(request):
            response.media = {'error': True, 'message': 'Not authorized'}
            return
        response.media = Serializer().list_models(name)

estimators_registry = dict()

def registry_add(project_name, model, sandbox, estimator):
    global estimators_registry
    estimators_registry[project_name] = (model, estimator)

class FitResourse:
    def on_post(self, request, response, name, version=None):
        if not check_token(request):
            response.media = {'error': True, 'message': 'Not authorized'}
            return
        response.media = fit_implementation(name, version, registry_add)

class PredictResourse:
    def on_post(self, request, response, name, version=None):
        if not check_token(request):
            response.media = {'error': True, 'message': 'Not authorized'}
            return
        global estimators_registry
        if name in estimators_registry:
            response.media = estimators_registry[name][1].predict(
                estimators_registry[name][0],
                json.loads(request.stream.read().decode())
            )
        else:
            response.media = implementation_predict(
                name, json.loads(request.stream.read().decode()), version
            )

class UIResource:
    def on_get(self, request, response, name=None):
        response.content_type = falcon.MEDIA_HTML
        response.status = falcon.HTTP_200
        with open('main.html', 'r') as htmlfile:
            response.data = htmlfile.read().encode()

class DashboardResource:
    def on_get(self, request, response, token):
        image = Serializer().read_project(
            os.path.join('saved_models', token)
        )['dashboard']
        response.content_type = falcon.MEDIA_HTML
        response.status = falcon.HTTP_200
        def wrap(picture):
            return """<html><head>
                      <style>
                        * {margin: 0;}
                        svg {max-width: 100%; max-height: 100vh;}
                      </style>
                      <head><body>
                      """ + picture + """
                      <script>
                      setTimeout(window.location.reload.bind(
                        window.location
                      ), 60 * 1000)</script>
                      </body></html>"""
        response.data = (wrap(image) if image else '').encode()

api = falcon.API(middleware=[MultipartMiddleware()])
api.add_route('/', UIResource())
api.add_route('/models/{name}', UIResource())
api.add_route('/projects/update', VersionResource())
api.add_route('/model/update', SettingsResource())
api.add_route('/projects/{name}', ModelsResource())
api.add_route('/projects/{name}/fit/', FitResourse())
api.add_route('/projects/{name}/fit/{version}', FitResourse())
api.add_route('/projects/{name}/predict/', PredictResourse())
api.add_route('/projects/{name}/predict/{version}', PredictResourse())
api.add_route('/projects', ProjectResource())
api.add_route('/dashboard/{token}', DashboardResource())
api.add_route('/login', LoginResource())

if not os.path.exists('saved_models'):
    os.makedirs('saved_models')