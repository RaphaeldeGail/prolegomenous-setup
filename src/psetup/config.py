"""Render a complete set of variables for the root structure.

The `config` module will look for a standard configuration file and a specific
environment file, both in YAML format, to generate the setup values to build
the root structure.

Typical usage example:

  setup = config.from_yaml()
"""

from yaml import safe_load
from schema import Schema, SchemaError
from google.cloud import resourcemanager_v3
from sys import prefix
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
        if isinstance(value, dict):
            dict1[key] = override(dict1[key], dict2[key])
        else:
            dict1[key] = dict2[key]
    return dict1

def from_yaml():
    """
    Fetch configuration entries for a particular root structure. The entries
    are supposed to be stored in YAML files.

    Returns:
        dict, the full configuration for the root structure.
    """
    # the schema for the environment file in YAML
    environment_schema = Schema({
        'google': {
            'organization': str,
            'billing_account': str,
            'ext_admin_user': str,
            'groups': {
                'finops_group': str,
                'admins_group': str,
                'policy_group': str,
                'executive_group': str
            }
        },
        'terraform': {
            'organization': str,
            'workspace_project': str
        }
    })

    # default file for configuration of the structure root
    default = f'{prefix}/config/psetup/default.yaml'

    if not path.isfile('environment.yaml'):
        raise RuntimeError('The file "environment.yaml" could not be found.')
    # load the environment from setup.yaml
    with open('environment.yaml', 'r', encoding='utf-8') as f:
        environment = safe_load(f)
    # validate the environment YAML against the schema
    try:
        environment_schema.validate(environment)
    except SchemaError as se:
        raise se

    if not path.isfile(default):
        raise RuntimeError(f'The file "{default}" could not be found.')
    with open(default, 'r', encoding='utf-8') as f:
        config = safe_load(f)

    if path.isfile('config.yaml'):
        with open('config.yaml', 'r', encoding='utf-8') as f:
            update = safe_load(f)
        config = override(config, update)

    # the organization number
    org_id = environment['google']['organization']
    ## the organization name as string 'organizations/{org_id}'
    parent = f'organizations/{org_id}'
    environment['parent'] = parent

    client = resourcemanager_v3.OrganizationsClient()
    request = resourcemanager_v3.GetOrganizationRequest(
        name=parent,
    )

    response = client.get_organization(request=request)

    environment['google']['org_name'] = response.display_name
    environment.update(config)

    return environment
