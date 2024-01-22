"""Client module for the psetup command-line.

This module define the command-line options of the client and the subsequent
list of subcommands. Each subcommand then leads to an executive function.
"""

from argparse import ArgumentParser
from pprint import pprint
from random import randint
from os import getenv
from google.cloud.billing_v1 import BillingAccount
from .config import from_yaml
from .utils import IamPolicy
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
    apply_service_account,
    control_access as service_account_access
)
from .tag import apply_key, control_access as tag_access
from .folder import apply_folder, control_access as folder_access

# Actions functions

def show(setup, args):

    # if pretty print
    if args.p:
        pprint(setup, indent=1, depth=2, compact=True)
        
        return None
    
    print(setup)
    
    return None

def role(setup, args):
    org = setup['google']['organization']['name']
    print('generating executive role... ', end='')
    name = 'executiveRole'
    executive_role = apply_role(parent=org, **(setup[name]))
    print('DONE')

    print('generating builder role... ', end='')
    name='builderRole'
    apply_role(parent=org, **(setup[name]))
    print('DONE')

    organization_iam = [{
        'role': executive_role.name,
        'members': [ f'group:{setup["google"]["groups"]["executive_group"]}' ]
    },
    {
        'role': 'roles/billing.admin',
        'members': [ f'group:{setup["google"]["groups"]["finops_group"]}' ]
    },
    {
        'role': 'roles/essentialcontacts.admin',
        'members': [ f'user:{setup["google"]["ext_admin_user"]}' ]
    },
    {
        'role': 'roles/iam.organizationRoleAdmin',
        'members': [ f'group:{setup["google"]["groups"]["admins_group"]}' ]
    },
    {
        'role': 'roles/orgpolicy.policyAdmin',
        'members': [ f'group:{setup["google"]["groups"]["policy_group"]}' ]
    },
    {
        'role': 'roles/resourcemanager.organizationAdmin',
        'members': [
            f'group:{setup["google"]["groups"]["admins_group"]}',
            f'user:{setup["google"]["ext_admin_user"]}'
        ]
    },
    {
        'role': 'roles/resourcemanager.organizationViewer',
        'members': [
            f'group:{setup["google"]["groups"]["finops_group"]}',
            f'group:{setup["google"]["groups"]["policy_group"]}'
        ]
    }]

    org_access(org, organization_iam)

    return None

def build(setup, args):

    org = setup['google']['organization']['name']
    bill = setup['google']['billing_account']
    tfc_org = setup['terraform']['organization']

    ##### Terraform Cloud #####

    print('generating Terraform Cloud project... ', end='')
    tfc_workspaces = apply_terraform(project='Workspaces', organization=tfc_org)

    print('DONE')

    ##### Root Project #####

    print('generating root project... ', end='')
    uuid = str(randint(1,999999))
    project = setup['rootProject']
    services = project.pop('services')
    project_id=f'{project["displayName"]}-{uuid}'

    root_project = apply_project(parent=org, project_id=project_id, **project)

    update_billing(project=root_project, billing_account_name=bill)

    enable_services(root_project, services)
    print('services enabled... ', end='')

    project_access(root_project, [{
        'role': 'roles/owner',
        'members': [ f'group:{setup["google"]["groups"]["executive_group"]}' ]
    }])
    print('IAM policy set... ', end='')

    print('DONE')

    ##### Workload Identity Pool #####
    pool_id = setup['organizationPool']['id']
    org_name = setup['google']['organization']['display_name']
    condition = f'organization:{tfc_org}:project:Workspaces'
    attribute_condition = f'assertion.sub.startsWith("{condition}")'
    oidc = {
        'allowedAudiences': [f'https://tfc.{org_name}'],
        'issuerUri': setup['terraformProvider']['oidc']['issuerUri']
    }

    print('generating workload identity pool... ', end='')
    organization_pool = apply_pool(
        project=root_project,
        pool_id=pool_id,
        description=setup['organizationPool']['description'],
        display_name=pool_id.replace('-', ' ').title()
    )

    apply_provider(
        parent = organization_pool,
        provider_id=setup['terraformProvider']['id'],
        description=setup['terraformProvider']['description'],
        display_name=setup['terraformProvider']['displayName'],
        oidc= oidc,
        attribute_mapping=setup['terraformProvider']['attributeMapping'],
        attribute_condition=attribute_condition
    )

    print('DONE')

    ##### Builder Service Account #####

    wrk_id = tfc_workspaces.id
    pool = f'principalSet://iam.googleapis.com/{organization_pool.name}'
    principal = f'{pool}/attribute.terraform_project_id/{wrk_id}'
    builder_account_iam = [
        {
            'role': 'roles/iam.serviceAccountTokenCreator',
            'members': [ f'group:{setup["google"]["groups"]["executive_group"]}' ]
        },
        {
            'role': 'roles/iam.workloadIdentityUser',
            'members': [ principal ]
        }
    ]

    print('generating service account... ', end='')
    builder_account = apply_service_account(
        project=root_project,
        account_id=setup['builderAccount']['name'],
        display_name=setup['builderAccount']['displayName'],
        description=setup['builderAccount']['description']
    )

    service_account_access(builder_account, builder_account_iam)
    print('IAM policy set... ', end='')

    print('DONE')

    ##### Workspace Tag #####
    builder_email = f'serviceAccount:{builder_account.email}'
    workspace_tag_key_iam = [{
        'role': 'roles/resourcemanager.tagAdmin',
        'members': [ builder_email ]
    }]

    print('generating workspace tag... ', end='')
    workspace_tag_key = apply_key(
        parent=setup['google']['organization']['name'],
        short_name=setup['workspaceTag']['shortName'],
        description=setup['workspaceTag']['description']
    )

    tag_access(workspace_tag_key, workspace_tag_key_iam)
    print('IAM policy set... ', end='')

    print('DONE')

    ##### Workspace Folder #####
    role  = setup['builderRole']['name']
    builder_role = f'{setup["google"]["organization"]["name"]}/roles/{role}'
    workspace_folder_iam = [{
        'role': 'roles/resourcemanager.folderAdmin',
        'members': [ f'group:{setup["google"]["groups"]["executive_group"]}' ]
    },
    {
        'role': builder_role,
        'members': [ builder_email ]
    }]

    print('generating workspace folder... ', end='')
    workspace_folder = apply_folder(
        parent=setup['google']['organization']['name'],
        display_name=setup['workspaceFolder']['displayName']
    )

    folder_access(workspace_folder, workspace_folder_iam)
    print('IAM policy set... ', end='')

    print('DONE')

    ##### END #####

    return None

def billing(setup, args):
    """
    Main entry for the psetup-billing client.

    """
    builder_email = getenv('BUILDER_EMAIL')

    if builder_email is None:
        raise ValueError('BUILDER_EMAIL environment variable empty')

    setup = from_yaml()
    mail = f'serviceAccount:{builder_email}'
    billing_account = f'billingAccounts/{setup["google"]["billing_account"]}'
    billing_account_iam = IamPolicy([
        {'members': [ mail ], 'role': 'roles/billing.user'},
        {'members': [ mail ], 'role': 'roles/billing.costsManager'},
        {'members': [ mail ], 'role': 'roles/iam.securityAdmin'}
    ])

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
    'epilog': 'More help on action commands with: %(prog)s {subcommand} -h.',
    'options': {
        '-f': {'dest': 'conf', 'help': 'Use a custom configuration file'},
        '-o': {'action': 'store_true', 'help': 'Stay offline'},
    }
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
        'func': show,
        'options': {
            '-p': {
                'help': 'Pretty print show on stdout',
                'action': 'store_true'
            }
        }
    },
    'role': {
        'description': 'Role setup for the root structure',
        'help': 'Setup the roles for the root structure',
        'func': role,
        'options': {}
    },
    'build': {
        'description': 'Build the root structure',
        'help': 'Build the root structure',
        'func': build,
        'options': {}
    },
    'billing': {
        'description': 'Billing setup for the root structure',
        'help': 'Setup the billing config for the root structure',
        'func': billing,
        'options': {}
    },
}

def set_options(parser, options):
    for option in options:
        option_config = options.get(option)
        parser.add_argument(option, **option_config)

    return None

def main():
    """Main function for psetup client.

    This function parses all options and subcommands from command-line. After
    generating a configuration for the root structure, it delegates the
    subsequent actions to specific action modules.
    """

    options = command.pop('options')
    parser = ArgumentParser(**command)
    set_options(parser, options)

    sub_command = actions.pop('metadata')
    subparsers = parser.add_subparsers(**sub_command)

    for action in actions:
        action_config = actions.get(action)
        options = action_config.pop('options')
        func = action_config.pop('func')
        action_parser = subparsers.add_parser(action, **action_config)
        action_parser.set_defaults(func=func)
        set_options(action_parser, options)

    # Parse arguments from command line
    args = parser.parse_args()

    # Read arguments values from config file
    setup = from_yaml(args.conf, args.o)

    # Launch the subcommand `main` function
    args.func(setup, args)
