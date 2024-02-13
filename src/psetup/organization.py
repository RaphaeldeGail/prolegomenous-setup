"""Manage a Google organization idempotently.

Can find a particular Google organization. The IAM policy can also be updated
or extended.

Typical usage example:

  org = organization.find('organizationName')
  organization.control(Organization, OrganizationPolicy)
  organization.add_control(Organization, OrganizationExtraPolicy)
"""

from google.cloud.resourcemanager_v3 import OrganizationsClient, SearchOrganizationsRequest
from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest, GetIamPolicyRequest

def find(display_name):
    """Get the existing organization corresponding to the declared resource.

    Args:
        display_name: string, the organization display name.

    Returns:
        google.cloud.resourcemanager_v3.types.Organization, the existing
            organization.

    Raises:
        IndexError, if there is no organization matching the declared resource.
        TypeError, if the matching organization is not unique.
    """
    # this is the query to find the matching projects
    query = f'domain:{display_name}'
    # instantiate the list of corresponding projects
    orgs = []

    client = OrganizationsClient()
    request = SearchOrganizationsRequest(query=query)

    page_result = client.search_organizations(request=request)

    for org in page_result:
        orgs.append(org)

    if len(orgs) > 1:
        e = TypeError([ org.name for org in orgs ])
        raise e

    try:
        org = orgs[0]
    except IndexError as exc:
        e = IndexError(0)
        raise e from exc

    return org

def control(organization, policy):
    """Apply IAM policy to the organization.

    Args:
        organization: google.cloud.resourcemanager_v3.types.Organization, the
            delcared organization.
        policy: google.iam.v1.policy_pb2.Policy, the policy to apply.
    """
    client = OrganizationsClient()
    request = SetIamPolicyRequest(
        resource=organization,
        policy=policy
    )

    client.set_iam_policy(request=request)

    return None

def add_control(organization, policy):
    """Add an extra IAM policy to the organization.

    Args:
        organization: google.cloud.resourcemanager_v3.types.Organization, the
            delcared organization.
        policy: google.iam.v1.policy_pb2.Policy, the extra policy to add.
    """
    client = OrganizationsClient()
    request = GetIamPolicyRequest(
        resource=organization,
    )

    response = client.get_iam_policy(request=request)

    response.bindings.MergeFrom(policy.bindings)
    request = SetIamPolicyRequest(
        resource=organization,
        policy=response
    )

    client.set_iam_policy(request=request)

    return None
