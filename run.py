#!/usr/bin/python

from google.auth import default
from googleapiclient.discovery import build
from yaml import safe_load
from os.path import basename
from os import environ
from jinja2 import Environment, select_autoescape, FileSystemLoader
from schema import Schema, SchemaError

# set global variables
## the schema for the setup file in YAML
config_schema = Schema({
    "google": {
        "organization": str,
        "billing_account": str,
        "ext_admin_user": str,
        "groups": {
            "finops_group": str,
            "admins_group": str,
            "policy_group": str,
            "executive_group": str
        }
    },
    "terraform": {
        "organization": str,
        "workspace_project": str
    }
})
## the scopes for all google API calls
scopes = ['https://www.googleapis.com/auth/cloud-platform']

# set the clients for google API role and IAM policy
# WARNING: the quota_project_id can not be set when calling the credentials
# default() method and has to be explicitly overidden with
# the with_quota_project(None) method.
cred = default(scopes=scopes)[0].with_quota_project(None)
project_api = build('cloudresourcemanager', 'v3', credentials=cred).projects()

def create_project(body):
    """
    Create a project with google API call.

    Args:
        parent: string, the organization ID.
        body: dict, the project to be created.

    Returns:
        dict, the project created.

    Raises:
        Exception: Raises an exception if the API call fails.
    """
    return {}

def set_project(parent, name='root'):
    """
    Set a project according to the project_data. Can either be create, update
    or leave it as it is.

    Args:
        parent: string, the name of the organization in
            the form organizations/{orgId}
        name: string, the project display Name. Defaults to 'root'.

    Returns:
        dict, the result project.
    """
    print(
        '[projects:{project}] setting up... '.format(project=name),
        end=''
    )
    # this is the query to find the project
    query = 'displayName={name} AND parent={parent} AND labels.root=true \
AND labels.uuid:* AND projectId:{name}-*'.format(parent=parent, name=name)
    request = project_api.search(query=query)
    try:
        result_project = request.execute()
    except:
        print('Error searching for projects.', end='')
    if not 'projects' in result_project:
        print('the project will be created... ', end='')
        # random UUID for the project
        uuid = 1234
        body = {
            "displayName": name,
            "labels": {
                "root": "true",
                "uuid": uuid
            },
            "parent": parent,
            "projectId": '{name}-{uuid}'.format(name=name, uuid=uuid),
        }
        result_project = create_project(body=body)
        if result_project is None:
            print('[ERROR] project creation failed')
            return None
        print('project successfully created.')
        return result_project
    else:
        print('the project is already up-to-date.')
        result_project = result_project['projects'][0]
    return result_project

# load the environment from setup.yaml
with open('setup.yaml', 'r') as f:
    setup = safe_load(f)
# validate the setup YAML against the schema
try:
    config_schema.validate(setup)
except SchemaError as se:
    raise se

# the organization number
org_id = setup['google']['organization']
## the organization name as string 'organizations/{org_id}'
parent = 'organizations/{org_id}'.format(org_id=org_id)

set_project(parent=parent)