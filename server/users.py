# dictionary user => password
import json

class Users:
    def __init__(self, jsonfile):
        self.jsonfile = jsonfile

    def __getitem__(self, key):
        with open(self.jsonfile, 'r') as fd:
            data = json.load(fd)
            if not key in data:
                return ''
            return data[key]

    def __iter__(self):
        with open(self.jsonfile, 'r') as fd:
            return json.load(fd).__iter__()

PROJECTS_USERS = Users('admins.json')
DASHBOARD_USERS = Users('users.json')
