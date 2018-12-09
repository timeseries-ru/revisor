import revisor as rv
import os

import pandas as pd
from sklearn import datasets

iris_dataset = datasets.load_iris()
dataframe = pd.DataFrame(iris_dataset.data, columns=iris_dataset.feature_names)
dataframe['target'] = iris_dataset.target

class ModelImplementation():
    def fit(self, model):
        data = model.get_dataset()

        features = list(data.columns)
        features.remove('target')

        X = data[features]
        y = data['target']

        self.classifier = linear.LogisticRegression(
            penalty = model.get_setting_value('penalty')
        ).fit(X, y)

        model.register_instance_on_server(self)

        if model.get_setting_value('visualize'):
            figure, axes = plt.subplots(1, figsize=(16, 9))
            axes.scatter(x=data[features[0]], y=data[features[1]], c=y)
            figure.tight_layout()
            model.set_dashboard_figure(figure)

        yield rv.Message().score('train_score', self.classifier.score(X, y))
        yield rv.Message().text('done')

    def predict(self, model, X):
        return self.classifier.predict(
            np.array(X).reshape(-1, model.get_dataset().shape[1] - 1)
        ).tolist()

revisor_url = os.environ['REVISOR_SITE'] if 'REVISOR_SITE' in os.environ \
              else 'http://localhost:8000'
project = rv.Project('ExampleProject - tests', revisor_url)

model = rv.Model('ExampleModel - version 1')
model.add_setting('penalty', 'l1 or l2', 'l2')
model.add_setting('visualize', 'bool', False)
model.add_setting('integer', 'integer', 1)
model.add_setting('float', 'float', 1e-4)
model.set_dataset(dataframe)

for short_name, module in [
    ('linear', 'sklearn.linear_model'),
    ('rv', 'revisor'),
    ('np', 'numpy'),
    ('plt', 'matplotlib.pyplot')
]: model.add_import(short_name, module)

project.set_description("Very basic sample project!")

token = 'a5be1b7a9aa52b5470848fb0c84d715fd7b5963d' # admin's token

# rewrites last deployed model
assert project.deploy(
    model, ModelImplementation, token, with_rewrite=True
)['ok']

# bump version
model.set_dataset(None)
model.set_name('ExampleModel')
model.set_setting('visualize', True)
assert project.deploy(
    model, ModelImplementation, token, with_rewrite=False
)['ok']

# reverse check
assert project.set_predictions_version(token, 2)['ok']

messages = project.fit(token, version=1)
print(messages)

messages = project.fit(token, version=2)
print(messages)

correct = dataframe['target'].values
dataframe = dataframe.drop('target', axis='columns')

predictions_left = project.predict(
    dataframe.values.tolist()[:len(correct) // 2],
    token
)

predictions_right = project.predict(
    dataframe.values.tolist()[len(correct) // 2:],
    token
)

from sklearn.metrics import classification_report
print(classification_report(correct, predictions_left + predictions_right))
