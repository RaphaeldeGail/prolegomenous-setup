from yaml import safe_load
from schema import Schema, SchemaError
from googleapiclient.discovery import build
import sys
from os import path

def override(dict1, dict2):
    """
    Override a dictionary entry, keys by keys subkeys by subkeys.

    Args:
        dict1: dict, the dictionnary to be updated.
        dict2: dict, the dictionnary with entries to be updated.

    Returns:
        dict, the updated dictionnary.
    """
    for key,value in dict1.items():
        if not key in dict2:
            continue
        if type(value) is dict:
            dict1[key] = override(dict1[key], dict2[key])
        else:
            dict1[key] = dict2[key]
    return dict1

def from_yaml(credentials):
    """
    Fetch configuration entries for a particular root structure. The entries
    are supposed to be stored in YAML files.

    Args:
        credentials: credentials, the user authentification to make a call.

    Returns:
        dict, the full configuration for the root structure.
    """
    # the schema for the environment file in YAML
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
    # validate the environment YAML against the schema
    try:
        environment_schema.validate(environment)
    except SchemaError as se:
        raise se

    if not path.isfile(default):
        raise RuntimeError('The file "{0}" could not be found.'.format(default))
    with open(default, 'r') as f:
        config = safe_load(f)

    if path.isfile('config.yaml'):
        with open('config.yaml', 'r') as f:
            update = safe_load(f)
        config = override(config, update)

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