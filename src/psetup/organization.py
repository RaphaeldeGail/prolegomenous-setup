"""Generate a root project idempotently.

Can apply a specific configuration for a root project and create or update it
in order to match the configuration.

Typical usage example:

  root_project = generate_root(setup)
"""

from google.cloud.resourcemanager_v3 import OrganizationsClient, SearchOrganizationsRequest
from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest

def find_organization(display_name):
    """Get the existing project corresponding to the declared project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the declared
            project.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the existing project if
            it is unique.

    Raises:
        IndexError, if there is no project matching the declared project.
        TypeError, if the matching project is not unique.
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

def control_access(organization, policy):
    """Apply IAM policy to the project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            project.
        policy: dict, list all `bindings` to apply to the project policy.
    """
    client = OrganizationsClient()
    request = SetIamPolicyRequest(
        resource=organization,
        policy=policy.format
    )

    client.set_iam_policy(request=request)

    return None
