# Revisor Library and UI Server
Revisor is a set of (two) tools for prediction models deploy, versioning and management:
1. Revisor python library gives you interface for pushing your models to server,
2. Revisor server gives the next facilities:

 -- HTML User Interface (with simple access restriction) for deployed models,

 -- Ability to fit them from UI and read what they have been logged,

 -- Ability to look through saved visualizations (as SVGs),

 -- Publish visualization as (one-minute reloading) dashboard page,

 -- API for making predictions with deployed models (JSON API),

 -- Change version of model for making predictions.


The solution *requires python 3.6+*. And, also, don't forget to track your original python code with **git** or JupyterLab Git Extension. This project dedicated to deploy-in-the-loop, not to code-in-the-loop.

## Installation
1. Clone this repo,
2. Install dependencies, the library itself and start the server.

From repository directory:
on Unix systems: start .shell files in scripts (you should look into them before),
on Windows system: start .batch files in scripts (you should look into them before).

## Screenshots (of samples models)
![Projects](images/projects.png?raw=1 "Projects")
![Models](images/models.png?raw=1 "Project models")


## Library Documentation
*To get quickly started, please look to few examples in Samples directory of this repository.*
Revisor library consists of three classes:

1. **Project**: project contains one or more models, that versions in it. Methods:

 -- init(*project_name*, *server_url*) - create project with specified name which will be used everywhere, and use Revisor server url (http://localhost:8000 by default).

 -- set_description(*description*) - set plain text description for your project (optional)

 -- deploy(*model_instance*, *implementation*, *token*, *with_rewrite*) - deploy model to server with given implementation, where first parameter is instance of class Model (described later), implementation - arbitrary class with mandatory **fit(self, model)** and **predict(self, model, data)** methods. With_rewrite parameter (is False by default) specifies if to rewrite the last deployed model or not (use with caution, only in development mode). The *token* shoud be obtained from the Server (UI). ***ATTENTION***: in Jupyter Notebooks the implementation MUST BE wrapped in function (returning class), otherwise it will not work.

2. **Model**: core class for containing model settings and other metadata (to be reused across) of your implementation. Methods:
 -- init(*name*) - create model with name,

 -- get_name, set_name(*name*) - get/set name of model,

 -- add_setting(*name*, *type*, *value*) - add setting to the model. Set of settings can be changed in UI (and therefore model can be refitted with them on server). The types are: 'integer' (validated), 'book' (checkbox representation), 'float' (validated) and arbitrary string (will be treated as string).

 -- set_dataset(*dataframe*) - set pandas.DataFrame object to be available (using model.get_dataset method) on the server, in your implementation. Will uploaded to the server! If current model version has no dataset, **get_dataset will return dataset of the previous version**.

 -- add_visualization(*image*, *description*) - **server only method** (can be called in your model implementation only). Add SVG (string) to the set of visualizations of model. Description is optional.

 -- add_visualization_figure(*figure*, *description*) - **server only**. Convenient method does the same as previous, but converts matplotlib figure to SVG (make sure matplotlib is installed on server).

 -- set_dashboard(*image*)/set_dashboard_figure(*figure*) - **server only**. Update project's dashboard.

 -- register_instance_on_server(*model_self*) - **server only**. Registers created model instance on server, which will be used for predictions (until server will not be restarted),

 -- open_file_on_server(*filename*, *open_mode*) - **server only**. Opens file with given mode on server.

3. **Message**: helper class to contain three types of messages can be yielded in fit of model implementation:
 -- score(*name*, *value*) - add name-value pair to fit log,

 -- text(*value*) - add simple text to fit log,

 -- error(*value*) - add error entry with text as value to fit log.


## Server API
Server API allows to take the predictions of deployed models (using defined "predict" method). To call it pass data as JSON array in POST request to
```
/projects/{your_project_plain_name}/predict/{optionally_give_a_model_version}
```
The results should be the predictions.

Default login/password for UI on server is admin/admin. Don't forget to change in users.py file in your server installation directory.

## Limitations
1. Certainly, I give NO WARRANTY! Only code.
2. The service is not suited for high performance tasks. For regular analitycs tasks is better.

## Issues and enhancements
Please fill found issues in this repository Issues Section, and new features requests (or ideas) send as pull requests. Thanks!
