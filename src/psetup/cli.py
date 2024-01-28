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
from .organization import (
    control_access as set_org_access,
    add_access as add_org_access
)
from .billing import control_access as set_billing_access
from .terraform import apply_project as apply_terraform
from .project import (
    apply_project,
    enable_services,
    update_billing,
    control_access as set_project_access
)
from .workload import apply_pool, apply_provider
from .service_account import (
    apply as apply_account,
    control_access as set_account_access
)
from .tag import apply_key, control_access as set_tag_access
from .folder import apply_folder, control_access as set_folder_access
from . import iam

# Actions functions

def show(setup):
    """Show values used for the root structure.

    Display the setup configuration values as a map on standard output.

    Args:
        setup: dict, the declared setup.
    """
    pprint(setup, indent=1, depth=2, compact=True)

    return None

def init(setup):
    """Initialize organization accesses.

    Set the IAM policy at the organization level for primary groups.

    Args:
        setup: dict, the declared setup.
    """
    org = setup['googleOrganization']['name']

    print('generating organization IAM policy... ', end='')

    set_org_access(org, iam.organization(setup))

    print('IAM policy set... ', end='')
    print('DONE')

    return None

def role(setup):
    """Create IAM roles for the root structure.

    Create the executive and builder roles at the organization level.

    Args:
        setup: dict, the declared setup.
    """
    org = setup['googleOrganization']['name']
    member = f'group:{setup["googleGroups"]["executive"]}'

    name = 'executiveRole'

    print(f'generating {name.split("Role", maxsplit=1)[0]} role... ', end='')

    executive_role = apply_role(parent=org, **(setup[name]))

    print('DONE')

    name='builderRole'

    print(f'generating {name.split("Role", maxsplit=1)[0]} role... ', end='')

    apply_role(parent=org, **(setup[name]))

    print('DONE')

    add_org_access(org, {'role': executive_role.name, 'members': [ member ]})

    print('IAM policy set... ', end='')
    print('DONE')

    return None

def build(setup):
    """Build the root structure.

    Create base resources from Terraform Cloud and Google Cloud.

    Args:
        setup: dict, the declared setup.
    """
    org = setup['googleOrganization']

    tfc_org = setup['terraformOrganization']
    tfc_prj = setup['terraformProject']

    uuid = str(randint(1,999999))
    project = setup['rootProject']
    project['id'] = f'{project["displayName"]}-{uuid}'

    services = project.pop('services')

    provider = setup['terraformProvider']
    condition = f'organization:{tfc_org}:project:{tfc_prj}'
    provider['attributeCondition'] = f'assertion.sub.startsWith("{condition}")'
    provider['oidc'] = {
        'allowedAudiences': [f'https://tfc.{org["displayName"]}'],
        'issuerUri': provider['oidc']['issuerUri']
    }

    account = setup['builderAccount']

    folder = setup['workspaceFolder']

    ##### Terraform Cloud #####

    print('generating Terraform Cloud project... ', end='')

    tfc_id = apply_terraform(project=tfc_prj, organization=tfc_org)

    print('DONE')

    ##### Root Project #####

    print('generating root project... ', end='')

    root_project = apply_project(parent=org['name'], **project)

    update_billing(project=root_project, name=setup['billingAccount'])

    print('billing updated... ', end='')

    enable_services(root_project, services)

    print('services enabled... ', end='')

    set_project_access(root_project, iam.project(setup))

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

    set_account_access(builder_account, iam.account(setup, org_pool, tfc_id))

    print('IAM policy set... ', end='')
    print('DONE')

    ##### Workspace Tag #####

    print('generating workspace tag... ', end='')

    workspace_tag_key = apply_key(parent=org['name'], **(setup['workspaceTag']))

    set_tag_access(workspace_tag_key, iam.workspace_tag(builder_account))

    print('IAM policy set... ', end='')
    print('DONE')

    ##### Workspace Folder #####

    print('generating workspace folder... ', end='')

    workspace_folder = apply_folder(parent=org['name'], **(folder))

    set_folder_access(
        workspace_folder,
        iam.workspace_folder(setup, builder_account)
    )

    print('IAM policy set... ', end='')
    print('DONE')

    ##### END #####

    return None

def billing(setup):
    """Configure the billing of the root structure.

    Add access to the root billing account for the builder account.

    Args:
        setup: dict, the declared setup.
    """
    builder_email = getenv('BUILDER_EMAIL')

    if builder_email is None:
        raise ValueError('BUILDER_EMAIL environment variable empty')

    billing_account_iam = iam.billing_account(builder_email)

    billing_account = BillingAccount(
        name=f'billingAccounts/{setup["billingAccount"]}'
    )

    ##### Billing Account #####

    print('generating billing account... ', end='')

    set_billing_access(billing_account, billing_account_iam)

    print('DONE')

    return None

command = {
    'prog': 'psetup',
    'description': 'Build an idempotent root structure.',
    'epilog': 'More help on action commands with: %(prog)s {subcommand} -h.'
}

options = {
    '-f': {'dest': 'config_file', 'help': 'Use a custom configuration file'},
}

sub_command = {
        'title': 'The Action Commands',
        'description': 'The different building steps of the %(prog)s command.',
        'help': 'Select one action, preferably following the list order.'
}

actions = [show, init, role, build, billing]

def main():
    """Main function for psetup client.

    This function parses all options and subcommands from command-line. After
    generating a configuration for the root structure, it delegates the
    subsequent actions to specific action function.
    """

    parser = ArgumentParser(**command)
    for option, config in options.items():
        parser.add_argument(option, **config)

    subparsers = parser.add_subparsers(**sub_command)

    for func in actions:
        docs = func.__doc__.split('\n\n')
        action_parser = subparsers.add_parser(
            func.__name__,
            help=docs[0],
            description=docs[1]
        )
        action_parser.set_defaults(func=func)

    # Parse arguments from command line
    args = parser.parse_args()

    # Read arguments values from custom config file
    setup = from_yaml(args.config_file)

    # Launch the subcommand function
    args.func(setup)
