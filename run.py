#!/usr/bin/python

from google.auth import default
from googleapiclient.discovery import build
from yaml import safe_load
from jinja2 import Environment, select_autoescape, FileSystemLoader
from schema import Schema, SchemaError
from time import sleep
import re

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
cloud_api = build('cloudresourcemanager', 'v3', credentials=cred)
iam_api = build('iam', 'v1', credentials=cred).projects().locations()
service_api = build('serviceusage', 'v1', credentials=cred)
## global organization setup data from the jinja template.
resources = Environment(
    loader=FileSystemLoader(searchpath='./resources/'),
    autoescape=select_autoescape()
)

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
        RuntimeError: Raises an exception if the API call does not return a
            successful response.
    """
    # the period is the number, in seconds, between two consecutive checks
    period = 5
    # error message if creation status times out
    status_timeout = 'timeout before project creation status is available.'
    # error message if creation completion times out
    completion_timeout = 'timeout before project creation is done.'
    create_request = cloud_api.projects().create(body=body)
    operation = create_request.execute()

    operation_request = cloud_api.operations().get(name=operation['name'])

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    operation = operation_request.execute()
    while not 'done' in operation:
        if time_elapsed > timeout % period :
            raise RuntimeError(status_timeout)
        time_elapsed += 1
        print('waiting for project creation status... ', end='')
        sleep(period)
        operation = operation_request.execute()

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while operation['done'] is False:
        if time_elapsed > timeout % period :
            raise RuntimeError(completion_timeout)
        time_elapsed += 1
        print('waiting for project creation to be done... ', end='')
        sleep(period)
        operation = operation_request.execute()
    return operation['response']

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
    # Declare the resource project
    # random UUID for the project
    uuid = 1234
    body = safe_load(
        resources.get_template('project.yaml.j2').render(
            name=name,
            parent=parent,
            uuid=str(uuid)
        )
    )['spec']
    print(
        '[projects:{project}] setting up... '.format(project=name),
        end=''
    )
    # Look for a project that already matches the declaration
    # this is the query to find the project
    query = 'displayName={name} AND parent={parent} AND labels.root=true \
AND labels.uuid:* AND projectId:{name}-*'.format(parent=parent, name=name)
    request = cloud_api.projects().search(query=query)
    try:
        result_projects = request.execute()
    except:
        print('Error searching for the root project.', end='')
    # If the project does not exist, create it
    if not 'projects' in result_projects:
        print('the project will be created... ', end='')
        result_project = create_project(body=body)
        print('project successfully created.')
        return result_project
    # Else, return the project data found
    projectId = result_projects['projects'][0]['projectId']
    uuid = re.search(r".*-([0-9]*)", projectId).group(1)
    if result_projects['projects'][0]['labels']['uuid'] != uuid:
        print('the project will be updated... ', end='')
        # update the project
        # return project resource
        print('project successfully updated.')
        return None
    print('the project is already up-to-date.')
    return result_projects['projects'][0]

def enable_service(name, timeout=60):
    """
    Enable a service in a project with google API call.

    Args:
        name: string, the name of the service in the format of 'projects/123/services/serviceusage.googleapis.com'.
        timeout: int, the timeout before service enabling fails, in seconds.
            defaults to 60 seconds.

    Returns:
        dict, the service enabled.

    Raises:
        RuntimeError: Raises an exception if the API call does not return a
            successful response.
    """
    # the period is the number, in seconds, between two consecutive checks
    period = 5
    # error message if creation status times out
    status_timeout = 'timeout before service enabling status is available.'
    # error message if creation completion times out
    completion_timeout = 'timeout before service enabling status is done.'
    enable_request = service_api.services().enable(name=name)
    operation = enable_request.execute()
    operation_request = service_api.operations().get(name=operation['name'])
    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    operation = operation_request.execute()
    while not 'done' in operation:
        if time_elapsed > timeout % period :
            raise RuntimeError(status_timeout)
        time_elapsed += 1
        print('waiting for service enabling status... ', end='')
        sleep(period)
        operation = operation_request.execute()

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while operation['done'] is False:
        if time_elapsed > timeout % period :
            raise RuntimeError(completion_timeout)
        time_elapsed += 1
        print('waiting for service enabling to be done... ', end='')
        sleep(period)
        operation = operation_request.execute()
        print(operation['done'])
    print(operation['done'])
    return operation['response']

def set_service(project):
    """
    Enable a list of services for a project, if they are not already enabled.
    Can either enable or leave it as it is.

    Args:
        project: string, the name of the projects in
            the form projects/{projectNumber}
        services: list(string), the list of services to be enabled.

    Returns:
        list, the complete list of enabled services in the project.
    """
    # load the service list
    services = safe_load(
        resources.get_template('project.yaml.j2').render(
            name='xxx',
            parent='xxx',
            uuid='xxx'
        )
    )['metadata']['services']
    print('[services] enabling... ', end='')
    enabled_services = service_api.services().list(parent=project, filter='state:ENABLED').execute()
    service_list = [ service['config']['name'] for service in enabled_services['services'] ]
    missing_services = list(set(services) - set(service_list))
    for service in missing_services:
            print('enabling {name}... '.format(name=service), end='')
            enable_service(name='{project}/services/{name}'.format(project=project, name=service))
    print('services succesfully enabled.')
    service_list.extend(missing_services)
    return service_list

def create_workload_identity(parent, body, name, timeout=60):
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
        RuntimeError: Raises an exception if the API call does not return a
            successful response.
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
            raise RuntimeError('timeout before workload identity pool creation status is available.')
        time_elapsed += 1
        print('waiting for workload identity pool creation status... ', end='')
        sleep(period)

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while request.execute()['done'] is False:
        if time_elapsed > timeout % period :
            raise RuntimeError('timeout before workload identity pool creation is done.')
        time_elapsed += 1
        print('waiting for workload identity pool creation to be done... ', end='')
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

def update_workload_identity(name, body, updateMask, timeout=60):
    """
    Update a workload identity with google API call.

    Args:
        name: string, the workload identity ID that will be part of the
            resource name.
        body: dict, the workload identity to be updated.
        updateMask: string, comma-separated keys that will be updated in the
            resource
        timeout: int, the timeout before project creation fails, in seconds.
            defaults to 60 seconds.

    Returns:
        dict, the workload identity created.

    Raises:
        RuntimeError: Raises an exception if the API call does not return a
            successful response.
    """
    period = 5
    request = iam_api.workloadIdentityPools().patch(
        name=name,
        body=body,
        updateMask=updateMask
    )
    operation = request.execute()
    request = iam_api.workloadIdentityPools().operations().get(
        name=operation['name']
    )
    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while not 'done' in request.execute():
        if time_elapsed > timeout % period :
            raise RuntimeError('timeout before workload identity pool update status is available.')
        time_elapsed += 1
        print('waiting for workload identity pool update status... ', end='')
        sleep(period)

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while request.execute()['done'] is False:
        if time_elapsed > timeout % period :
            print('workload identity pools failed to be updated.', end='')
            raise RuntimeError('timeout before workload identity pool update is done.')
        time_elapsed += 1
        print('waiting for workload identity pool update to be done... ', end='')
        sleep(period)
    request = iam_api.workloadIdentityPools().get(name=name)
    return request.execute()

def set_workload_identity(project, name='organization-identity-pool'):
    """
    Set a workload identity pool. Can either be create, update or leave it as it is.

    Args:
        project: string, the project where the workload identity pool resides. In
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
    # Declare the resource workload identity pool
    body = safe_load(
        resources.get_template('workload.yaml.j2').render(
            org_name=org_name,
            display_name=name.replace('-', ' ').title()
        )
    )
    print(
        '[workloadIdentityPools:{name}] setting up... '.format(name=name),
        end=''
    )
    # Look for a workload identity pool that already matches the full name
    request = iam_api.workloadIdentityPools().get(name=full_name)
    try:
        result_workload = request.execute()
    # If the workload identity pool does not exist, create it
    except:
        print('the workload identity will be created... ', end='')

        result_workload = create_workload_identity(parent=parent, body=body, name=name)
        print('workload successfully created.')
        return result_workload
    if result_workload['state'] == 'DELETED':
        print('[ERROR] the workload identity exists but is in DELETED state.')
        print('Please undo the DELETED state before proceeding.')
        return None
    # compare the workload identity pool declared and the one existing
    diff = dict(body.items() - result_workload.items())
    if 'displayName' in diff or 'description' in diff:
        print('the workload identity will be updated... ', end='')
        # update the workload
        result_workload = update_workload_identity(
            name=full_name,
            body=body,
            updateMask=','.join(diff.keys())
        )
        print('workload successfully updated.')
        return result_workload
    print('workload identity is already up-to-date.')
    return result_workload

def create_identity_provider(parent, body, name, timeout=60):
    """
    Create a workload identity provider with google API call.

    Args:
        parent: string, the workload identity provider where the provider resides. In
            the form projects/{projectNumber}/locations/global/workloadIdentityPools/{name}.
        body: dict, the provider to be created.
        name: string, the workload identity provider ID that will be part of the
            resource name.
        timeout: int, the timeout before creation fails, in seconds.
            defaults to 60 seconds.

    Returns:
        dict, the workload identity provider created.

    Raises:
        Exception: Raises an exception if the API call fails.
    """
    return {}

def set_identity_provider(workload, terraform_org, name='tfc-oidc'):
    """
    Set a workload identity provider. Can either be create, update or leave it
    as it is.

    Args:
        workload: string, the name of the workload identity provider resource.
        terraform_org: string, the name of the Terraform Cloud organization
            that will be used to provide identities for the Google Cloud
            organization.
        name: string, the name of the provider for the workload.

    Returns:
        dict, the result workload identity provider.
    """
    provider_file='provider.yaml.j2'
    # The name of the provider resource in Google Cloud fashion
    full_name = '{wrkId}/providers/{name}'.format(wrkId=workload, name=name)
    # Declare the resource provider
    body = safe_load(
        resources.get_template(provider_file).render(
            terraform_org=terraform_org,
            org_name=org_name
        )
    )
    print(
        '[identityProviders:{name}] setting up... '.format(name=name),
        end=''
    )
    # Look for an already existing provider
    request = iam_api.workloadIdentityPools().providers().get(name=full_name)
    try:
        result_provider = request.execute()
    except:
        print('the identity provider will be created... ', end='')
        result_provider = create_identity_provider(parent=workload, body=body, name=name)
        print('identity provider successfully created.')
        return result_provider
    # compare the workload identity pool declared and the one existing
    updateMask = []
    for key in set(body.keys()).intersection(result_provider.keys()):
        if body[key] != result_provider[key]:
            updateMask.append(key)
    if updateMask != []:
        print('the identity provider will be updated... ', end='')
        # update provider
    print('identity provider is already up-to-date.')
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
## the organization display name
org_name = cloud_api.organizations().get(name=parent).execute()['displayName']
print('Organization name: ' + org_name)

root_project = set_project(parent=parent)
print(root_project)
enabled_services = set_service(project=root_project['name'])
print(enabled_services)
wrk_id = set_workload_identity(project=root_project['name'])
print(wrk_id)
provider = set_identity_provider(
    workload=wrk_id['name'],
    terraform_org=setup['terraform']['organization']
)
print(provider)
# Close all connections
cloud_api.close()
iam_api.close()
service_api.close()