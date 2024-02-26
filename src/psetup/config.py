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
    for key, value in update.items():
        if key not in base:
            base[key] = value
        elif isinstance(value, dict):
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
    config = {}
    default_system_config = f'{prefix}/config/psetup/default.yaml'
    default_user_config = f'{USER_BASE}/config/psetup/default.yaml'

    for file in [default_system_config, default_user_config, custom_config]:
        if file and isfile(file):
            files.append(file)
            with open(file, 'r', encoding='utf-8') as f:
                update = safe_load(f)
            config = _override(config, update)

    if not files:
        raise FileNotFoundError('No default configuration file')

    return config

def from_env(name):
    value = getenv(name)

    if not value:
        raise KeyError('Environment variable not found', name)
