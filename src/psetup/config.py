"""Render a complete set of variables for the root structure.

The `config` module will look for a standard configuration file and a specific
environment file, both in YAML format, to generate the setup values to build
the root structure.

Typical usage example:

  setup = config.from_yaml()
"""

from yaml import safe_load
from sys import prefix
from site import USER_BASE
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

def from_yaml(custom_config):
    """
    Fetch configuration entries for a particular root structure. The entries
    are supposed to be stored in YAML files.

    Returns:
        dict, the full configuration for the root structure.
    """

    default_config = f'{prefix}/config/psetup/default.yaml'
    if not isfile(default_config):
        default_config = f'{USER_BASE}/config/psetup/default.yaml'

    google_organization = getenv('GOOGLE_ORGANIZATION', None)
    google_billing_account = getenv('GOOGLE_BILLING_ACCOUNT', None)
    external_owner = getenv('EXTERNAL_OWNER', None)
    finops_group = getenv('FINOPS_GROUP', None)
    admins_group = getenv('ADMINS_GROUP', None)
    policy_group = getenv('POLICY_GROUP', None)
    executive_group = getenv('EXECUTIVE_GROUP', None)
    tfc_organization = getenv('TFC_ORGANIZATION', None)

    environment = {
        'googleOrganization': { 'displayName': google_organization },
        'billingAccount': google_billing_account,
        'owner':  external_owner,
        'googleGroups': {
            'finops': finops_group,
            'admins': admins_group,
            'policy': policy_group,
            'executive': executive_group
        },
        'terraformOrganization': tfc_organization
    }

    # Load data from default configuration file
    try:
        with open(default_config, 'r', encoding='utf-8') as f:
            config = safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError('Default configuration file not found') from e

    # Load data from user configuration file
    try:
        with open(custom_config, 'r', encoding='utf-8') as f:
            update = safe_load(f)
        config = _override(config, update)
    except TypeError:
        pass

    # Fetch organization data
    org_domain = environment['googleOrganization']['displayName']
    org = find_organization(org_domain)

    environment['googleOrganization']['name'] = org.name
    dci = org.directory_customer_id
    environment['googleOrganization']['directoryCustomerId'] = dci
    # Merge all data
    environment.update(config)

    return environment
