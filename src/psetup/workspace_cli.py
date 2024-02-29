"""Client module for the wsetup command-line.

This module define the command-line options of the client and the executive
function to create a workspace.
"""

from argparse import ArgumentParser
from yaml import safe_load
from os import getenv
from terrasnek.api import TFC

from .config import from_env
from .terraform_workspace import (
    apply as apply_workspace,
    apply_variable as apply_wrk_variable
)

def workspace(wconfile):
    """Create a workspace in a root structure.

    Create the resources for a workspace to live in a "Workspaces" folder.

    Args:
        setup: dict, the declared setup.
        wconf: string, the file of the workspace configuration.
    """
    tfc_org = from_env('TFC_ORGANIZATION')
    tfc_prj = from_env('TFC_PROJECT')

    # Read arguments values from custom config file
    with open(wconfile, 'r', encoding='utf-8') as f:
        setup = safe_load(f)

    name = setup['name']
    budget_allowed = setup['budgetAllowed']
    admin_group = setup['adminGroup']
    finops_group = setup['finopsGroup']
    policy_group = setup['policyGroup']
    provider = setup['provider']

    description = ''
    if 'description' in setup:
        description = setup['description']
    repo_id = 'RaphaeldeGail/workspace-nucleation'
    if 'repoId' in setup:
        repo_id = setup['repoId']

    print('Fetch oauth token id... ')

    TFC_TOKEN = getenv('TFC_TOKEN')
    TFC_URL = getenv('TFC_URL', 'https://app.terraform.io')

    api = TFC(TFC_TOKEN, url=TFC_URL)
    api.set_org(tfc_org)

    oclients = api.oauth_clients.list()

    oauth_token = None
    for oclient in oclients.get('data', []):
        if oclient['attributes']['name'] == provider:
            oauth_tokens = oclient['relationships']['oauth-tokens']['data']
            oauth_token = oauth_tokens[0]['id']

    print('DONE')
    print('Generate a terraform workspace... ')

    wrk = apply_workspace(
        name=name,
        org_id=tfc_org,
        project=tfc_prj,
        repo_id=repo_id,
        description=description,
        oauth_token=oauth_token
    )

    print('DONE')
    print('generating variables inside variable set... ')

    apply_wrk_variable(
        org_id=tfc_org,
        wrk_id=wrk.id,
        key='budget_allowed',
        value=str(budget_allowed),
        sensitive=False,
        category='terraform',
        hcl=False,
        description='the maximum spending amount allowed for the workspace.'
    )
    apply_wrk_variable(
        org_id=tfc_org,
        wrk_id=wrk.id,
        key='admin_group',
        value=admin_group,
        sensitive=False,
        category='terraform',
        hcl=False,
        description='Email for administrators group of the workspace.'
    )
    apply_wrk_variable(
        org_id=tfc_org,
        wrk_id=wrk.id,
        key='policy_group',
        value=policy_group,
        sensitive=False,
        category='terraform',
        hcl=False,
        description='Email for policy administrators group of the workspace.'
    )
    apply_wrk_variable(
        org_id=tfc_org,
        wrk_id=wrk.id,
        key='finops_group',
        value=finops_group,
        sensitive=False,
        category='terraform',
        hcl=False,
        description='Email for finops group of the workspace.'
    )

    print('DONE')

    return None

command = {
    'prog': 'wsetup',
    'description': 'Create a workspace',
    'epilog': 'More help on action commands with: %(prog)s -h.'
}

options = {
    'Wconfile': {'help': 'The workspace declaration file'},
}

def main():
    """Main function for wsetup client.

    This function parses all options from command-line. It then delegates the
    subsequent workspace creation to a specific executive function.
    """
    parser = ArgumentParser(**command)
    for option, config in options.items():
        parser.add_argument(option, **config)

    # Parse arguments from command line
    args = parser.parse_args()

    # Launch the workspace creation function
    workspace(args.Wconfile)
