"""Client module for the psetup command-line.

This module define the command-line options of the client and the subsequent
list of subcommands. Each subcommand then leads to an executive function.
"""

from argparse import ArgumentParser
from pprint import pprint
from random import randint
from google.iam.v1.policy_pb2 import Policy
# local imports
from .config import from_yaml, from_env
from .role import apply as apply_role
from .organization import (
    control as set_org_access,
    add_control as add_org_access,
    find as find_organization
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

def show(args):
    """Show the values used for a root structure.

    Display the setup configuration as a map on standard output. Long entries
    will be cut on display. No authentication required.

    Args:
        args: Namespace, the arguments from command line.
    """
    # Read arguments values from custom config file
    setup = from_yaml(args.config_file)

    pprint(setup, indent=1, depth=2, compact=True)

    return None

def init(args):
    """Initializes the organization access.

    Set the IAM policy at the organization level for the top-level groups. If
    you initialize an organization with a root structure, you will be set back
    to top-level group access and lose almost all access to your root
    structure. You should authenticate as the owner of the Google organization
    for this action.

    Args:
        args: Namespace, the arguments from command line.
    """
    if args.config_file:
        print('WARNING, unused flag "-f" for the "init" action.')

    org = from_env('GOOGLE_ORGANIZATION')
    owner = from_env('EXTERNAL_OWNER')
    admins = from_env('ADMINS_GROUP')
    finops = from_env('FINOPS_GROUP')
    policy = from_env('POLICY_GROUP')

    # Fetch organization data
    org_name = find_organization(org).name

    print('Generating organization IAM policy... ')

    set_org_access(org_name, iam.organization(owner, admins, finops, policy))

    print('DONE')

    return None

def role(args):
    """Creates the IAM roles for a root structure.

    Creates the "executive" and "builder" IAM roles at the organization level.
    Existing roles will be updated or left as it is, according to the setup
    plan. Updates the organization access according to the new roles. You
    should authenticate as an "Organization Administrator" on Google Cloud for
    this action.

    Args:
        args: Namespace, the arguments from command line.
    """
    org = from_env('GOOGLE_ORGANIZATION')
    member = f'group:{from_env("EXECUTIVE_GROUP")}'

    # Fetch organization data
    org_name = find_organization(org).name

    # Read arguments values from custom config file
    setup = from_yaml(args.config_file)

    name = 'executiveRole'

    print(f'Generating {name.split("Role", maxsplit=1)[0]} role... ')

    executive_role = apply_role(parent=org_name, **(setup[name]))

    print('DONE')

    name='builderRole'

    print(f'Generating {name.split("Role", maxsplit=1)[0]} role... ')

    apply_role(parent=org_name, **(setup[name]))

    print('DONE')

    print('Extending organization IAM policy... ')

    policy = Policy()
    policy.bindings.add(role=executive_role.name, members=[ member ])

    add_org_access(org_name, policy)

    print('DONE')

    return None

def build(args):
    """Builds the elements of a root structure.

    Creates the various resources on Terraform Cloud and Google Cloud. Existing
    resources will be updated or left as it is, according to the setup plan.
    You should authenticate as an "Organization Executive" on Google Cloud for
    this action, as well as an "Organization Owner" on Terraform Cloud.

    Args:
        args: Namespace, the arguments from command line.
    """
    org = from_env('GOOGLE_ORGANIZATION')
    executives = from_env('EXECUTIVE_GROUP')
    tfc_org = from_env('TFC_ORGANIZATION')
    billing_account = from_env('GOOGLE_BILLING_ACCOUNT')

    # Fetch organization data
    org_data = find_organization(org)
    org_name = org_data.name
    org_directory = org_data.directory_customer_id

    # Read arguments values from custom config file
    setup = from_yaml(args.config_file)

    tfc_prj = setup['terraformProject']

    uuid = str(randint(1,999999))
    project = setup['rootProject']
    project['project_id'] = f'{project["displayName"]}-{uuid}'

    services = project.pop('services')

    provider = setup['terraformProvider']
    condition = f'organization:{tfc_org}:project:{tfc_prj}'
    provider['attributeCondition'] = f'assertion.sub.startsWith("{condition}")'
    provider['oidc'] = {
        'allowedAudiences': [f'https://tfc.{org}'],
        'issuerUri': provider['oidc']['issuerUri']
    }

    account = setup['builderAccount']

    folder = setup['workspaceFolder']

    ##### Terraform Cloud Project #####

    print('Generating Terraform Cloud project... ')

    tfc_prj = apply_terraform(name=tfc_prj, org_id=tfc_org)

    print('DONE')

    ##### Root Project #####

    print('Generating root project... ')

    root_project = apply_project(parent=org_name, **project)

    update_billing(project=root_project, name=billing_account)

    print('... billing updated... ')

    enable_services(root_project, services)

    print('... services enabled... ')

    set_project_access(root_project, iam.project(executives))

    print('... IAM policy set... ')
    print('DONE')

    ##### Workload Identity Pool #####

    print('Generating organization identities pool... ')

    org_pool = apply_pool(project=root_project, **(setup['organizationPool']))

    provider = apply_provider(parent = org_pool, **provider)

    print('DONE')

    ##### Builder Service Account #####

    print('Generating builder service account... ')

    builder_account = apply_account(project=root_project, **(account))

    policy = iam.account(executives, org_pool, tfc_prj.id)
    set_account_access(builder_account, policy)

    print('... IAM policy set... ')
    print('DONE')

    ##### Workspace Tag #####

    print('Generating workspace tag... ')

    workspace_tag_key = apply_key(parent=org_name, **(setup['workspaceTag']))

    set_tag_access(workspace_tag_key, iam.workspace_tag(builder_account))

    print('... IAM policy set... ')
    print('DONE')

    ##### Workspace Folder #####

    print('Generating workspace folder... ')

    workspace_folder = apply_folder(parent=org_name, **(folder))

    set_folder_access(
        workspace_folder,
        iam.workspace_folder(setup, builder_account, executives, org_name)
    )

    print('... IAM policy set... ')
    print('DONE')

    ##### Terraform Variable Sets #####

    print('Generating variable set... ')

    creds_varset = apply_variableset(
        org_id=tfc_org,
        name=setup['credentialsVariableSet']['name'],
        description=setup['credentialsVariableSet']['description'],
        project=tfc_prj.id
    )

    apply_variable(
        org_id=tfc_org,
        varset_id=creds_varset.id,
        key='project',
        value=root_project.project_id,
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
        value=billing_account.split('/')[-1],
        sensitive=True,
        category='terraform',
        hcl=False,
        description='The ID of the billing account used for the workspaces.',
    )
    apply_variable(
        org_id=tfc_org,
        varset_id=org_varset.id,
        key='organization',
        value=org,
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
        value=org_directory,
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

def billing(args):
    """Creates the 'Billing Users' group for a root structure.

    Creates the 'Billing Users' google group and add the builder account as its
    manager. You should authenticate as a "FinOps" on Google Cloud for this
    action.

    Args:
        args: Namespace, the arguments from command line.
    """
    org = from_env('GOOGLE_ORGANIZATION')
    billing_account = from_env('GOOGLE_BILLING_ACCOUNT')
    billing_email = from_env('BILLING_GROUP')

    # Fetch organization data
    org_data = find_organization(org)
    org_name = org_data.name
    org_directory = org_data.directory_customer_id

    # Read arguments values from custom config file
    setup = from_yaml(args.config_file)

    project = setup['rootProject']
    project['project_id'] = project['displayName']
    project.pop('services')

    print('Looking for builder account... ')

    project = apply_project(parent=org_name, **project)

    domain = f'{project.project_id}.iam.gserviceaccount.com'
    builder_account = f'{setup["builderAccount"]["name"]}@{domain}'

    print('DONE')

    ##### Google Group #####

    print('Generate a Billing Google group... ')

    billing_group = apply_group(
        parent=f'customers/{org_directory}',
        email=billing_email,
        **(setup['billingGroup'])
    )

    print('DONE')

    ##### IAM Policy #####

    print('Set IAM access for the group... ')

    set_billing_access(billing_account, iam.billing_account(billing_email))

    print('DONE')

    ##### Group Member#####

    print('Add the builder account to the group... ')

    apply_membership(
        parent=billing_group.name,
        email=builder_account,
        roles=['MANAGER', 'MEMBER']
    )

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
        'description': '''The different building steps of the %(prog)s command.
            Each requires a different Google Cloud authentication and/or
            Terraform Cloud authentication.''',
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

    # Launch the subcommand function
    args.func(args)
