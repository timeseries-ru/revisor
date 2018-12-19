import revisor as rv

def ClassWrapper():
  class Implementation:
    def task(self, model):
      print("Code will print this text every minute")
    def fit(self, model):
      import revisor # you'll need to reimport modules
      print("Code can be called using API or server UI")
      yield revisor.Message().text("Text to be logged")
    def predict(self, model, array):
      print("Code can be called using API")
      return reversed(array)
  return Implementation

token = 'a5be1b7a9aa52b5470848fb0c84d715fd7b5963d'

project = rv.Project("Project Name")
model = rv.Model("Model name")
project.deploy(model, ClassWrapper, token, with_rewrite=True)

print(project.fit(token))
