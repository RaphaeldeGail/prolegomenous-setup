"""Render a complete set of variables for the root structure.

The `config` module will look for a standard configuration file and a specific
environment file, both in YAML format, to generate the setup values to build
the root structure. Standard configuration is first read and then its entries
are superseded by any present in the custom configuration.

Typical usage example:

  setup = config.from_yaml()
"""

from yaml import safe_load
from sys import prefix
from site import USER_BASE
from os.path import isfile
from os import getenv

from .organization import find as find_organization

def _override(base, update):
    """Override a dictionary entry, keys by keys subkeys by subkeys.

    Args:
        base: dict, the dictionnary to be updated.
        update: dict, the dictionnary that updates.

    Returns:
        dict, the updated dictionnary.
    """
    for key,value in update.items():
        if isinstance(value, dict):
            base[key] = _override(base[key], value)
        else:
            base[key] = value
    return base

def from_yaml(custom_config=None):
    """Fetch configuration entries for a particular root structure.
    
    The configuration entries are supposed to be stored in YAML files. The
    default file comes in the PyPi package and the custom one remains optional.
    Users may need it to override specific entries. The function also fetch
    environment values from environment variables to complete the
    configuration.

    Args:
        custom_config: str, a user-specified file for the configuration.
            Defaults to None.

    Returns:
        dict, the full configuration for the root structure.

    Raises:
        FileNotFoundError: if no configuration file is found.
    """
    files = []
    default_system_config = f'{prefix}/config/psetup/default.yaml'
    default_user_config = f'{USER_BASE}/config/psetup/default.yaml'

    if isfile(default_system_config):
        files.append(default_system_config)
    if isfile(default_user_config):
        files.append(default_user_config)
    if custom_config and isfile(custom_config):
        files.append(custom_config)

    if not files:
        raise FileNotFoundError('No default configuration file')

    google_organization = getenv('GOOGLE_ORGANIZATION', None)
    google_billing_account = getenv('GOOGLE_BILLING_ACCOUNT', None)
    external_owner = getenv('EXTERNAL_OWNER', None)
    finops_group = getenv('FINOPS_GROUP', None)
    admins_group = getenv('ADMINS_GROUP', None)
    policy_group = getenv('POLICY_GROUP', None)
    executive_group = getenv('EXECUTIVE_GROUP', None)
    tfc_organization = getenv('TFC_ORGANIZATION', None)

    # Fetch organization data
    org = find_organization(google_organization)

    environment = {
        'googleOrganization': {
            'name': org.name,
            'displayName': google_organization,
            'directoryCustomerId': org.directory_customer_id
        },
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

    config = {}
    # Load data from default configuration file
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            update = safe_load(f)
        config = _override(config, update)

    environment.update(config)

    return environment
