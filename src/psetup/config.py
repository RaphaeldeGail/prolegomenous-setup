from yaml import safe_load
from schema import Schema, SchemaError
from googleapiclient.discovery import build
import sys

def from_yaml(credentials):
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

    # load the environment from setup.yaml
    with open('setup.yaml', 'r') as f:
        setup = safe_load(f)
    # validate the setup YAML against the schema
    try:
        config_schema.validate(setup)
    except SchemaError as se:
        raise se
    
    with open('{0}/config/psetup/default.yaml'.format(sys.prefix), 'r') as f:
        config = safe_load(f)

    # the organization number
    org_id = setup['google']['organization']
    ## the organization name as string 'organizations/{org_id}'
    parent = 'organizations/{org_id}'.format(org_id=org_id)
    setup['parent'] = parent
    with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
        org_name = api.organizations().get(name=parent).execute()['displayName']
    setup['google']['org_name'] = org_name
    setup.update(config)
    
    return setup