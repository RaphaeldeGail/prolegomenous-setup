"""Client module for the psetup command-line.

This module define the command-line options of the client and the subsequent
list of subcommands. Each subcommand then leads to an executive function.
"""

from argparse import ArgumentParser
from pprint import pprint
from random import randint
from google.iam.v1.policy_pb2 import Policy
# local imports
from .config import from_yaml
from .role import apply as apply_role
from .organization import (
    control as set_org_access,
    add_control as add_org_access
)
from .terraform import apply as apply_terraform
from .terraform_variable import apply_variableset, apply_variable
from .project import (
    apply as apply_project,
    services as enable_services,
    billing as update_billing,
    control as set_project_access
)
from .workload import apply_pool, apply_provider
from .service_account import (
    apply as apply_account,
    control as set_account_access
)
from .tag import apply as apply_key, control as set_tag_access
from .folder import apply as apply_folder, control as set_folder_access
from .identity import apply_group, apply_membership
from .billing import control as set_billing_access
from . import iam

# Actions functions

def show(setup):
    """Show the values used for a root structure.

    Display the setup configuration as a map on standard output. Long entries
    will be cut on display.

    Args:
        setup: dict, the declared setup.
    """
    pprint(setup, indent=1, depth=2, compact=True)

    return None

def init(setup):
    """Initialize the organization access.

    Set the IAM policy at the organization level for the top-level groups. If
    you initialize an organization with a root structure, you will be set back
    to top-level group access and lose almost all access to your root
    structure.

    Args:
        setup: dict, the declared setup.
    """
    org = setup['googleOrganization']['name']

    print('generating organization IAM policy... ')

    set_org_access(org, iam.organization(setup))

    print('DONE')

    return None

def role(setup):
    """Create the IAM roles for a root structure.

    Create the "executive" and "builder" IAM roles at the organization level.
    Existing roles will be updated or left as it is, according to the setup
    plan.

    Args:
        setup: dict, the declared setup.
    """
    org = setup['googleOrganization']['name']
    member = f'group:{setup["googleGroups"]["executive"]}'

    name = 'executiveRole'

    print(f'generating {name.split("Role", maxsplit=1)[0]} role... ')

    executive_role = apply_role(parent=org, **(setup[name]))

    print('DONE')

    name='builderRole'

    print(f'generating {name.split("Role", maxsplit=1)[0]} role... ')

    apply_role(parent=org, **(setup[name]))

    print('DONE')

    print('extending organization IAM policy... ')

    policy = Policy()
    policy.bindings.add(role=executive_role.name, members=[ member ])

    add_org_access(org, policy)

    print('DONE')

    return None

def build(setup):
    """Build the elements of a root structure.

    Create the various resources on Terraform Cloud and Google Cloud. Existing
    resources will be updated or left as it is, according to the setup plan.

    Args:
        setup: dict, the declared setup.
    """
    org = setup['googleOrganization']

    tfc_org = setup['terraformOrganization']
    tfc_prj = setup['terraformProject']

    uuid = str(randint(1,999999))
    project = setup['rootProject']
    project['project_id'] = f'{project["displayName"]}-{uuid}'

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

    ##### Terraform Cloud Project #####

    print('generating Terraform Cloud project... ')

    tfc_id = apply_terraform(name=tfc_prj, org_id=tfc_org)

    print('DONE')

    ##### Root Project #####

    print('generating root project... ')

    root_project = apply_project(parent=org['name'], **project)

    update_billing(project=root_project, name=setup['billingAccount'])

    print('... billing updated... ')

    enable_services(root_project, services)

    print('... services enabled... ')

    set_project_access(root_project, iam.project(setup))

    print('... IAM policy set... ')
    print('DONE')

    ##### Workload Identity Pool #####

    print('generating organization identities pool... ')

    org_pool = apply_pool(project=root_project, **(setup['organizationPool']))

    provider = apply_provider(parent = org_pool, **provider)

    print('DONE')

    ##### Builder Service Account #####

    print('generating builder service account... ')

    builder_account = apply_account(project=root_project, **(account))

    set_account_access(builder_account, iam.account(setup, org_pool, tfc_id.id))

    print('... IAM policy set... ')
    print('DONE')

    ##### Workspace Tag #####

    print('generating workspace tag... ')

    workspace_tag_key = apply_key(parent=org['name'], **(setup['workspaceTag']))

    set_tag_access(workspace_tag_key, iam.workspace_tag(builder_account))

    print('... IAM policy set... ')
    print('DONE')

    ##### Workspace Folder #####

    print('generating workspace folder... ')

    workspace_folder = apply_folder(parent=org['name'], **(folder))

    set_folder_access(
        workspace_folder,
        iam.workspace_folder(setup, builder_account)
    )

    print('... IAM policy set... ')
    print('DONE')

    ##### Terraform Variable Sets #####

    print('generating variable set... ')

    creds_varset = apply_variableset(
        org_id=tfc_org,
        name=setup['credentialsVariableSet']['name'],
        description=setup['credentialsVariableSet']['description'],
        project=tfc_id.id
    )

    apply_variable(
        org_id=tfc_org,
        varset_id=creds_varset.id,
        key='project',
        value=tfc_id.id,
        sensitive=True,
        category='terraform',
        hcl=False,
        description='The ID of the root project for the organization. \
            Used to create workspaces.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=creds_varset.id,
        key='TFC_GCP_WORKLOAD_PROVIDER_NAME',
        value=provider.name,
        sensitive=False,
        category='env',
        hcl=False,
        description='The canonical name of the workload identity provider.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=creds_varset.id,
        key='TFC_GCP_WORKLOAD_IDENTITY_AUDIENCE',
        value=provider.oidc['allowedAudiences'][0],
        sensitive=False,
        category='env',
        hcl=False,
        description='Will be used as the aud claim for the identity token.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=creds_varset.id,
        key='TFC_GCP_PROVIDER_AUTH',
        value='true',
        sensitive=False,
        category='env',
        hcl=False,
        description='Must be present and set to true, or Terraform Cloud will \
            not attempt to use dynamic credentials to authenticate to GCP.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=creds_varset.id,
        key='TFC_GCP_RUN_SERVICE_ACCOUNT_EMAIL',
        value=builder_account.email,
        sensitive=True,
        category='env',
        hcl=False,
        description='The service account email Terraform Cloud will use when \
            authenticating to GCP.',
    )

    org_varset = apply_variableset(
        org_id=tfc_org,
        name=setup['organizationVariableSet']['name'],
        description=setup['organizationVariableSet']['description'],
        glob=True
    )

    apply_variable(
        org_id=tfc_org,
        varset_id=org_varset.id,
        key='billing_account',
        value=setup['billingAccount'].split('/')[-1],
        sensitive=True,
        category='terraform',
        hcl=False,
        description='The ID of the billing account used for the workspaces.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=org_varset.id,
        key='organization',
        value=org['displayName'],
        sensitive=False,
        category='terraform',
        hcl=False,
        description='Name or domain of the organization hosting the workspace.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=org_varset.id,
        key='region',
        value='europe-west1',
        sensitive=False,
        category='terraform',
        hcl=False,
        description='Geographical *region* for Google Cloud Platform.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=org_varset.id,
        key='workspaces_tag_key',
        value=workspace_tag_key.name,
        sensitive=False,
        category='terraform',
        hcl=False,
        description='The ID of \\\"workspace\\\" tag key.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=org_varset.id,
        key='customer_directory',
        value=org['directoryCustomerId'],
        sensitive=False,
        category='terraform',
        hcl=False,
        description='The ID of the Google Cloud Identity directory.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=org_varset.id,
        key='workspaces_folder',
        value=workspace_folder.name.split('/')[-1],
        sensitive=False,
        category='terraform',
        hcl=False,
        description='The ID of the \\\"Workspaces\\\" folder that contains all \
            subsequent workspaces.',
    )

    print('DONE')

    ##### END #####

    return None

def billing(setup):
    """Create the 'Billing Users' group for a root structure.

    Create the 'Billing Users' google group and add the builder account as its
    manager.

    Args:
        setup: dict, the declared setup.
    """
    #create a google group
    #set billingAccountUser permission for group on billing account
    #add builder account as group manager
    org = setup['googleOrganization']['name']

    directory = setup['googleOrganization']['directoryCustomerId']

    project = setup['rootProject']
    project['project_id'] = project['displayName']
    project.pop('services')

    account = setup['builderAccount']

    print('Looking for builder account... ')

    project = apply_project(parent=org, **project)

    builder_account = f'{setup["builderAccount"]["name"]}@{project.project_id}.iam.gserviceaccount.com'

    print('DONE')
    print('Generate a Billing Google group... ')

    billing_group = apply_group(parent=f'customers/{directory}', **(setup['billingGroup']))

    print('DONE')
    print('Set IAM access for the group... ')

    set_billing_access()

    print('DONE')
    print('Add the builder account to the group... ')

    apply_membership(parent=billing_group.name, email=builder_account, roles=['MANAGER', 'MEMBER'])

    print('DONE')

    return None

# Base client configuration

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
    subsequent actions to specific executive function.
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
