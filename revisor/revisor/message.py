class Message():
    def score(self, name, value):
        return {
            'type': 'score',
            'name': name,
            'value': value
        }

    def text(self, value):
        return {
            'type': 'text',
            'value': value
        }

    def error(self, message):
        return {
            'type': 'error',
            'value': message
        }
