"""Produce IAM policies for Cloud resources.

For each resource, a function of this module will render its IAM policy.

Typical usage example:

  organization_policy = iam.organization(setup='rootStructureSetup')
"""

from google.iam.v1.policy_pb2 import Policy

from .config import from_env
from .organization import find as find_organization

def organization(owner, admins, finops, policy):
    """Returns the IAM policy for the Google organization.

    Args:
        setup: dict, the declared configuration for the root structure.

    Returns:
        google.iam.v1.policy_pb2.Policy, the resulting IAM policy.
    """
    prefix = 'roles/resourcemanager.organization'
    adm = f'group:{admins}'
    fin = f'group:{finops}'
    pol = f'group:{policy}'
    ownr = f'user:{owner}'

    iam = Policy()
    iam.bindings.add(role='roles/billing.admin', members=[fin])
    iam.bindings.add(role='roles/iam.organizationRoleAdmin', members=[adm])
    iam.bindings.add(role='roles/orgpolicy.policyAdmin', members=[pol])
    iam.bindings.add(role=f'{prefix}Admin', members=[adm, ownr])
    iam.bindings.add(role=f'{prefix}Viewer', members=[fin, pol])

    return iam

def project(executives):
    """Returns the IAM policy for the root project.

    Args:
        setup: dict, the declared configuration for the root structure.

    Returns:
        google.iam.v1.policy_pb2.Policy, the resulting IAM policy.
    """
    exe = f'group:{executives}'

    iam = Policy()
    iam.bindings.add(role='roles/owner', members=[exe])

    return iam

def account(executives, pool, tfc_project):
    """Returns the IAM policy for the builder account.

    Args:
        setup: dict, the declared configuration for the root structure.
        pool: string, the fully-qualified name of the organization identity
            workload pool provider.
        tfc_project: string, the ID of the terraform Workspace project.

    Returns:
        google.iam.v1.policy_pb2.Policy, the resulting IAM policy.
    """
    prefix = f'principalSet://iam.googleapis.com/{pool.name}'
    principal = f'{prefix}/attribute.terraform_project_id/{tfc_project}'
    exe = f'group:{executives}'

    iam = Policy()
    iam.bindings.add(role='roles/iam.serviceAccountTokenCreator', members=[exe])
    iam.bindings.add(role='roles/iam.workloadIdentityUser', members=[principal])

    return iam

def workspace_tag(builder_account):
    """Returns the IAM policy for the Workspace tag.

    Args:
        builder_account: psetup.service_account.ServiceAccount, the builder
            service account.

    Returns:
        google.iam.v1.policy_pb2.Policy, the resulting IAM policy.
    """
    build = f'serviceAccount:{builder_account.email}'

    iam = Policy()
    iam.bindings.add(role='roles/resourcemanager.tagAdmin', members=[build])

    return iam

def workspace_folder(setup, builder_account, executives, org_name):
    """Returns the IAM policy for the Workspace folder.

    Args:
        setup: dict, the declared configuration for the root structure.
        builder_account: psetup.service_account.ServiceAccount, the builder
            service account.

    Returns:
        google.iam.v1.policy_pb2.Policy, the resulting IAM policy.
    """
    builder_role = f'{org_name}/roles/{setup["builderRole"]["name"]}'
    build = f'serviceAccount:{builder_account.email}'
    exe = f'group:{executives}'

    iam = Policy()
    iam.bindings.add(role='roles/resourcemanager.folderAdmin', members=[exe])
    iam.bindings.add(role=builder_role, members=[build])

    return iam

def billing_account(billing_group):
    """Returns the IAM policy for the billing account.

    Args:
        setup: dict, the declared configuration for the root structure.

    Returns:
        google.iam.v1.policy_pb2.Policy, the resulting IAM policy.
    """
    bill = f'group:{billing_group}'

    iam = Policy()
    iam.bindings.add(role='roles/billing.user', members=[bill])

    return iam