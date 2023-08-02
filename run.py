#!/usr/bin/python

from google.auth import default
from googleapiclient.discovery import build
from yaml import safe_load
from os.path import basename
from os import environ
from jinja2 import Environment, select_autoescape, FileSystemLoader
from schema import Schema, SchemaError
from time import sleep

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
ops_api = build('cloudresourcemanager', 'v3', credentials=cred).operations()
iam_api = build('iam', 'v1', credentials=cred).projects().locations()

def create_project(body, timeout=60):
    """
    Create a project with google API call.

    Args:
        parent: string, the organization ID.
        body: dict, the project to be created.
        timeout: int, the timeout before project creation fails, in seconds.
            defaults to 60 seconds.

    Returns:
        dict, the project created.

    Raises:
        Exception: Raises an exception if the API call fails.
    """
    # the period is the number, in seconds, between two consecutive checks
    period = 5
    request = project_api.create(body=body)
    operation = request.execute()

    request = ops_api.get(name=operation['name'])

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while not 'done' in request.execute():
        if time_elapsed > timeout % period :
            print('project failed to be created', end='')
            return None
        time_elapsed += 1
        print('waiting for project to be created.', end='')
        sleep(period)

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while request.execute()['done'] is False:
        if time_elapsed > timeout % period :
            print('project failed to be created.', end='')
            return None
        time_elapsed += 1
        print('waiting for project to be created.', end='')
        sleep(period)
    return request.execute()['response']

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
                "uuid": str(uuid)
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

def create_workload(parent, body, name, timeout=60):
    """
    Create a workload identity with google API call.

    Args:
        parent: string, the project where the workload identity resides. In
            the form projects/{projectNumber}.
        body: dict, the workload identity to be created.
        name: string, the workload identity ID that will be part of the
            resource name.
        timeout: int, the timeout before project creation fails, in seconds.
            defaults to 60 seconds.

    Returns:
        dict, the workload identity created.

    Raises:
        Exception: Raises an exception if the API call fails.
    """
    # the period is the number, in seconds, between two consecutive checks
    period = 5
    request = iam_api.workloadIdentityPools().create(
        parent=parent,
        body=body,
        workloadIdentityPoolId=name
    )
    try:
        operation = request.execute()
    except Exception as err:
        raise err('Operation read request failed.')

    request = iam_api.workloadIdentityPools().operations().get(
        name=operation['name']
    )
    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while not 'done' in request.execute():
        if time_elapsed > timeout % period :
            print('workload identity pools failed to be created', end='')
            return None
        time_elapsed += 1
        print('waiting for workload identity pools to be created.', end='')
        sleep(period)

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while request.execute()['done'] is False:
        if time_elapsed > timeout % period :
            print('workload identity pools failed to be created.', end='')
            return None
        time_elapsed += 1
        print('waiting for workload identity pools to be created.', end='')
        sleep(period)

    # the operations method does not return any error or response data after
    # completion so you have to call the get method to return the workload
    # identity data
    full_name = '{parent}/workloadIdentityPools/{name}'.format(
        parent=parent,
        name=name
    )
    request = iam_api.workloadIdentityPools().get(name=full_name)
    return request.execute()

def set_workload_identity(project, name='organization-identity-pool'):
    """
    Set a workload_identity. Can either be create, update or leave it as it is.

    Args:
        project: string, the project where the workload identity resides. In
            the form projects/{projectNumber}.
        name: string, the workload identity ID that will be part of the
            resource name. Defaults to 'organization-identity-pool'.

    Returns:
        dict, the result workload identity.
    """
    # full name for workload identity is of the form
    # projects/{number}/locations/global/workloadIdentityPools/{workloadId}
    parent = '{project}/locations/global'.format(project=project)
    full_name = '{parent}/workloadIdentityPools/{name}'.format(
        parent=parent,
        name=name
    )
    print(
        '[workloadIdentityPools:{name}] setting up... '.format(name=name),
        end=''
    )
    request = iam_api.workloadIdentityPools().get(name=full_name)
    try:
        result_workload = request.execute()
    except:
        print('the workload identity will be created... ', end='')
        body = {
            "description": 'Workload identity pool for the organization.',
            "disabled": False,
            "displayName": name.replace('-', ' ').title()
        }
        result_workload = create_workload(parent=parent, body=body, name=name)
        if result_workload is None:
            print('[ERROR] role creation failed')
            return None
        print('workload successfully created.')
        return result_workload
    if result_workload['state'] == 'DELETED':
        print('[ERROR] the workload identity exists but is in DELETED state.')
        print('Please undo the DELETED state before proceeding.')
        return None
    print('workload identity already exists.')
    return result_workload

def create_provider(parent, body, name, timeout=60):
    """
    Create a workload identity with google API call.

    Args:
        parent: string, the workload identity where the provider resides. In
            the form projects/{projectNumber}/locations/global/workloadIdentityPools/{name}.
        body: dict, the provider to be created.
        name: string, the workload identity provider ID that will be part of the
            resource name.
        timeout: int, the timeout before project creation fails, in seconds.
            defaults to 60 seconds.

    Returns:
        dict, the workload provider created.

    Raises:
        Exception: Raises an exception if the API call fails.
    """
    return {}

def set_workload_provider(workload, terraform_org, name='tfc-oidc'):
    """
    Set a workload identity provider. Can either be create, update or leave it
    as it is.

    Args:
        workload: string, the name of the workload identity resource.
        terraform_org: string, the name of the Terraform Cloud organization
            that will be used to provide identities for the Google Cloud
            organization.
        name: string, the name of the provider for the workload.

    Returns:
        dict, the result workload identity provider.
    """
    full_name = '{wrkId}/providers/{name}'.format(wrkId=workload, name=name)
    print(
        '[workloadProviders:{name}] setting up... '.format(name=name),
        end=''
    )
    request = iam_api.workloadIdentityPools().providers().get(name=full_name)
    try:
        result_provider = request.execute()
    except:
        print('the workload provider will be created... ', end='')
        body = {
            'attributeCondition': 'assertion.sub.startsWith("organization:{org}:project:Workspaces")'.format(org=terraform_org),
            "attributeMapping": {
                "a_key": "A String",
            },
            "description": "A String",
            "disabled": False,
            "displayName": "A String",
            "oidc": {
                "allowedAudiences": [
                    "A String",
                ],
                "issuerUri": "A String"
            }
        }
        result_provider = create_provider(parent=workload, body=body, name=name)
        if result_provider is None:
            print('[ERROR] workload provider creation failed')
            return None
        print('workload provider successfully created.')
        return result_provider
    print('workload provider already exists.')
    return result_provider

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

root_project = set_project(parent=parent)
# print(root_project)
wrk_id = set_workload_identity(project=root_project['name'])
# print(wrk_id)
provider = set_workload_provider(workload=wrk_id['name'], terraform_org=setup['terraform']['organization'])
# print(provider)