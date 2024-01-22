"""Render a complete set of variables for the root structure.

The `config` module will look for a standard configuration file and a specific
environment file, both in YAML format, to generate the setup values to build
the root structure.

Typical usage example:

  setup = config.from_yaml()
"""

from yaml import safe_load
from sys import prefix
from os.path import isfile
from os import getenv

from .organization import find_organization

def _override(dict1, dict2):
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
            dict1[key] = _override(dict1[key], dict2[key])
        else:
            dict1[key] = dict2[key]
    return dict1

def from_yaml(file, offline):
    """
    Fetch configuration entries for a particular root structure. The entries
    are supposed to be stored in YAML files.

    Returns:
        dict, the full configuration for the root structure.
    """
    default = f'{prefix}/config/psetup/default.yaml'

    google_organization = getenv('GOOGLE_ORGANIZATION', None)
    google_billing_account = getenv('GOOGLE_BILLING_ACCOUNT', None)
    external_owner = getenv('EXTERNAL_OWNER', None)
    finops_group = getenv('FINOPS_GROUP', None)
    admins_group = getenv('ADMINS_GROUP', None)
    policy_group = getenv('POLICY_GROUP', None)
    executive_group = getenv('EXECUTIVE_GROUP', None)
    tfc_organization = getenv('TFC_ORGANIZATION', None)

    environment = {}
    environment['google'] = {
        'organization': {
            'display_name': google_organization
        },
        'billing_account': google_billing_account,
        'ext_admin_user': external_owner,
        'groups': {
            'finops_group': finops_group,
            'admins_group': admins_group,
            'policy_group': policy_group,
            'executive_group': executive_group
        }
    }
    environment['terraform'] = {
        'organization': tfc_organization
    }

    # Load data from default configuration file
    if not isfile(default):
        raise RuntimeError(f'The file "{default}" could not be found.')
    with open(default, 'r', encoding='utf-8') as f:
        config = safe_load(f)

    # Load data from user configuration file
    if file and isfile(file):
        with open(file, 'r', encoding='utf-8') as f:
            update = safe_load(f)
        config = _override(config, update)

    # Fetch organization data
    org_domain = environment['google']['organization']['display_name']
    if not offline:
        org = find_organization(org_domain)

        environment['google']['organization']['name'] = org.name
        dci = org.directory_customer_id
        environment['google']['organization']['directory_customer_id'] = dci
    # Merge all data
    environment.update(config)

    return environment
