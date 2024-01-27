"""Client module for the psetup command-line.

This module define the command-line options of the client and the subsequent
list of subcommands. Each subcommand then leads to an executive function.
"""

from argparse import ArgumentParser
from pprint import pprint
from random import randint
from os import getenv
from google.cloud.billing_v1 import BillingAccount
# local imports
from .config import from_yaml
from .role import apply_role
from .organization import control_access as org_access
from .billing import control_access
from .terraform import apply_project as apply_terraform
from .project import (
    apply_project,
    enable_services,
    update_billing,
    control_access as project_access
)
from .workload import apply_pool, apply_provider
from .service_account import (
    apply_account,
    control_access as account_access
)
from .tag import apply_key, control_access as tag_access
from .folder import apply_folder, control_access as folder_access
from . import iam

# Actions functions

def show(setup):
    """Show values of root structure.

    Show the setup configuration values.

    Args:
        setup: dict, the declared setup.
        args: argparse.Namespace, namespace of arguments from command-line.
    """
    pprint(setup, indent=1, depth=2, compact=True)

    return None

def role(setup):
    """Role setup for the root structure.

    Setup the roles for the root structure.

    Args:
        setup: dict, the declared setup.
        args: argparse.Namespace, namespace of arguments from command-line.
    """
    org = setup['google']['organization']['name']

    name = 'executiveRole'

    print('generating executive role... ', end='')
    executive_role = apply_role(parent=org, **(setup[name]))
    print('DONE')

    name='builderRole'

    print('generating builder role... ', end='')
    apply_role(parent=org, **(setup[name]))
    print('DONE')

    org_access(org, iam.organization(setup, executive_role))
    print('IAM policy set... ', end='')
    print('DONE')

    return None

def build(setup):
    """Build the root structure.

    Build the root structure.

    Args:
        setup: dict, the declared setup.
        args: argparse.Namespace, namespace of arguments from command-line.
    """
    org = setup['googleOrganization']

    tfc_org = setup['terraformOrganization']
    tfc_prj = setup['terraformProject']

    uuid = str(randint(1,999999))
    project = setup['rootProject']
    project['id'] = f'{project["displayName"]}-{uuid}'

    services = project.pop('services')

    provider = setup['terraformProvider']
    condition = f'organization:{tfc_org}:project:{setup["terraformProject"]}'
    provider['attributeCondition'] = f'assertion.sub.startsWith("{condition}")'
    provider['oidc'] = {
        'allowedAudiences': [f'https://tfc.{org["displayName"]}'],
        'issuerUri': provider['oidc']['issuerUri']
    }

    account = setup['builderAccount']

    folder = setup['workspaceFolder']

    ##### Terraform Cloud #####

    print('generating Terraform Cloud project... ', end='')
    tfc_wrk = apply_terraform(project=tfc_prj, organization=tfc_org)

    print('DONE')

    ##### Root Project #####

    print('generating root project... ', end='')
    root_project = apply_project(parent=org['name'], **project)

    update_billing(project=root_project, name=setup['billingAccount'])
    print('billing updated... ', end='')

    enable_services(root_project, services)
    print('services enabled... ', end='')

    project_access(root_project, iam.project(setup))
    print('IAM policy set... ', end='')

    print('DONE')

    ##### Workload Identity Pool #####

    print('generating organization identities pool... ', end='')
    org_pool = apply_pool(project=root_project, **(setup['organizationPool']))

    apply_provider(parent = org_pool, **provider)

    print('DONE')

    ##### Builder Service Account #####

    print('generating builder service account... ', end='')
    builder_account = apply_account(project=root_project, **(account))

    account_access(builder_account, iam.account(setup, org_pool, tfc_wrk))
    print('IAM policy set... ', end='')

    print('DONE')

    ##### Workspace Tag #####

    print('generating workspace tag... ', end='')
    workspace_tag_key = apply_key(parent=org['name'], **(setup['workspaceTag']))

    tag_access(workspace_tag_key, iam.workspace_tag(builder_account))
    print('IAM policy set... ', end='')

    print('DONE')

    ##### Workspace Folder #####

    print('generating workspace folder... ', end='')
    workspace_folder = apply_folder(parent=org['name'], **(folder))

    folder_access(
        workspace_folder,
        iam.workspace_folder(setup, builder_account)
    )
    print('IAM policy set... ', end='')

    print('DONE')

    ##### END #####

    return None

def billing(setup):
    """Setup the billing config for the root structure.

    Billing setup for the root structure.

    Args:
        setup: dict, the declared setup.
        args: argparse.Namespace, namespace of arguments from command-line.
    """
    builder_email = getenv('BUILDER_EMAIL')

    if builder_email is None:
        raise ValueError('BUILDER_EMAIL environment variable empty')

    billing_account = f'billingAccounts/{setup["billingAccount"]}'
    billing_account_iam = iam.billing_account(builder_email)

    billing_account = BillingAccount(
        name=billing_account
    )

    ##### Billing Account #####

    print('generating billing account... ', end='')
    control_access(billing_account, billing_account_iam)

    print('DONE')

    return None

command = {
    'prog': 'psetup',
    'description': 'Build an idempotent root structure.',
    'epilog': 'More help on action commands with: %(prog)s {subcommand} -h.'
}

options = {
    '-f': {'dest': 'conf', 'help': 'Use a custom configuration file'},
}

actions = {
    'metadata': {
        'title': 'The Action Commands',
        'description': 'The different building steps of the %(prog)s command.',
        'help': 'Select one action, preferably following the list order.',
    },
    'show': {
        'description': 'Show values of root structure',
        'help': 'Show the setup configuration values',
        'func': show
    },
    'role': {
        'description': 'Role setup for the root structure',
        'help': 'Setup the roles for the root structure',
        'func': role
    },
    'build': {
        'description': 'Build the root structure',
        'help': 'Build the root structure',
        'func': build
    },
    'billing': {
        'description': 'Billing setup for the root structure',
        'help': 'Setup the billing config for the root structure',
        'func': billing
    },
}

def main():
    """Main function for psetup client.

    This function parses all options and subcommands from command-line. After
    generating a configuration for the root structure, it delegates the
    subsequent actions to specific action function.
    """

    parser = ArgumentParser(**command)
    for option in options:
        option_config = options.get(option)
        parser.add_argument(option, **option_config)

    sub_command = actions.pop('metadata')
    subparsers = parser.add_subparsers(**sub_command)

    for action in actions:
        action_config = actions.get(action)
        func = action_config.pop('func')
        action_parser = subparsers.add_parser(action, **action_config)
        action_parser.set_defaults(func=func)

    # Parse arguments from command line
    args = parser.parse_args()

    # Read arguments values from config file
    setup = from_yaml(args.conf)

    # Launch the subcommand `main` function
    args.func(setup)
