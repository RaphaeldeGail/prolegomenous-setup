from yaml import safe_load
from schema import Schema, SchemaError
from googleapiclient.discovery import build
import sys
from os import path

def from_yaml(credentials):
    # set global variables
    ## the schema for the setup file in YAML
    environment_schema = Schema({
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

    # default file for configuration of the structure root
    default = '{0}/config/psetup/default.yaml'.format(sys.prefix)

    if not path.isfile('environment.yaml'):
        raise RuntimeError('The file "environment.yaml" could not be found.')
    # load the environment from setup.yaml
    with open('environment.yaml', 'r') as f:
        environment = safe_load(f)
    # validate the setup YAML against the schema
    try:
        environment_schema.validate(environment)
    except SchemaError as se:
        raise se

    if not path.isfile(default):
        raise RuntimeError('The file "{0}" could not be found.'.format(default))
    with open(default, 'r') as f:
        config = safe_load(f)

    # the organization number
    org_id = environment['google']['organization']
    ## the organization name as string 'organizations/{org_id}'
    parent = 'organizations/{org_id}'.format(org_id=org_id)
    environment['parent'] = parent
    with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
        org_name = api.organizations().get(name=parent).execute()['displayName']
    environment['google']['org_name'] = org_name
    environment.update(config)
    
    return environment