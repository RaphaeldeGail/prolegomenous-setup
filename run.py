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

def create_project(parent, body):
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
    return

# load the environment from setup.yaml
with open('setup.yaml', 'r') as f:
    setup = safe_load(f)
# validate the setup YAML against the schema
try:
    config_schema.validate(setup)
except SchemaError as se:
    raise se