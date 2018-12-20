import falcon
import json
import os

from serializer import Serializer, hashing
from falcon_multipart.middleware import MultipartMiddleware

from executor import fit_implementation, implementation_predict,\
                     bump_version, bump_settings, implementation_tasks

import xml.etree.cElementTree as etree

import schedule, threading, time, atexit

def is_svg(source):
    tag = None
    try:
        tag = etree.fromstring(source).tag
    except etree.ParseError:
        pass
    return tag == '{http://www.w3.org/2000/svg}svg'

from users import PROJECTS_USERS, DASHBOARD_USERS

def check_token(request):
    if not 'token' in request.cookies:
        return False
    token = request.cookies['token']
    for user in PROJECTS_USERS:
        if hashing(PROJECTS_USERS[user]) == token:
            return True
    return False

def check_user_token(request):
    if not 'token' in request.cookies:
        return False
    token = request.cookies['token']
    for user in DASHBOARD_USERS:
        if hashing(DASHBOARD_USERS[user]) == token:
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
            elif 'dashboard' in data:
                if data['dashboard']:
                    user = data['name']
                    if hashing(DASHBOARD_USERS[user]) == hashing(data['pass']):
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
    def on_get(self, request, response):
        if not check_token(request):
            response.media = {'error': True, 'message': 'Not authorized'}
            return
        data = json.loads(request.stream.read().decode())
        result = Serializer().read_project(Serializer().get_folder_name(
            data['project'] if 'project' in data else ''
        ))
        response.media = {"predictions_model": result['predictions_model']} \
            if 'predictions_model' in result else result
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

def registry_add(project_name, model, estimator):
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

visdown_start = """
<html><head></head><body>
<div id="contents"></div>
<div id="original" style="display: none;">
"""

visdown_end = """
</div>
<script src="https://cdn.jsdelivr.net/npm/vega@4.3.0"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@3.0.0-rc10"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@3.24.1"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/markdown-it/8.4.2/markdown-it.min.js"></script>
<script>
setTimeout(window.location.reload.bind(
  window.location
), 60 * 1000)
function initialization() {
    var md = window.markdownit();
    var specs = [];
    function parse_vega(tokens, idx, options, env, self) {
      specs.push(JSON.parse(tokens[idx].content));
      return "<div id='vega_" + specs.length + "'></div>";
    };
    function create_csv_download(tokens, idx, options, env, self) {
      return "<div><a href='data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(
        tokens[idx].content.slice(5)
      ) + "' download='data.csv' style='text-align: center; display: block;'>CSV</a></div>";
    };
    function parse_blocks(tokens, idx, options, env, self) {
        if (tokens[idx].content.slice(0, 5) === 'data:') {
            return create_csv_download(tokens, idx, options, env, self);
        } else {
            return parse_vega(tokens, idx, options, env, self);
        }
    }
    md.renderer.rules.fence = parse_blocks;
    document.getElementById(
        'contents'
    ).innerHTML =  md.render(
        document.getElementById('original').innerHTML
    );
    for (let index = 0; index < specs.length; ++index)
        vegaEmbed('#vega_' + (index + 1).toString(), specs[index], {actions: false});
};
document.addEventListener('DOMContentLoaded', initialization, false);
</script>
</body></html>
"""

def wrap_image(picture):
    return """<html><head>
              <style>
                * {margin: 0;}
                svg {max-width: 100%; max-height: 100vh;}
              </style>
              </head><body>
              """ + picture + """
              <script>
              setTimeout(window.location.reload.bind(
                window.location
              ), 60 * 1000)</script>
              </body></html>"""

class DashboardResource:
    def on_get(self, request, response, token):
        if not check_token(request):
            if not check_user_token(request):
                response.content_type = falcon.MEDIA_HTML
                response.status = falcon.HTTP_200
                with open('login.html', 'r') as htmlfile:
                    response.data = htmlfile.read().encode()
                return
        project = Serializer().read_project(
            os.path.join('saved_models', token)
        )
        if not 'dashboard' in project:
            return
        dashboard = project['dashboard']
        response.content_type = falcon.MEDIA_HTML
        response.status = falcon.HTTP_200
        if not dashboard:
            return
        if len(dashboard) == 2:
            response.data = (
                visdown_start.replace(
                    "<head></head>",
                    "<head><style>" + dashboard[1] + "</style></head>"
                ) + dashboard[0] + visdown_end
            ).encode()
        elif is_svg(dashboard): # we have an image
            response.data = (
                wrap_image(dashboard) if dashboard else ''
            ).encode()

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

def job():
    implementation_tasks()

schedule.every(60).seconds.do(job)
continuous_run = threading.Event()
class ScheduleThread(threading.Thread):
    daemon = True
    @classmethod
    def run(cls):
        while not continuous_run.is_set():
            schedule.run_pending()
            time.sleep(5)

continuous_thread = ScheduleThread()
continuous_thread.start()

def exit_handler():
    continuous_run.set()
    continuous_thread.join()

atexit.register(exit_handler)
