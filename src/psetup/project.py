"""Generate a project idempotently.

Can apply a specific configuration for a project and create or update it in
order to match the configuration. The project services can then be enabled and
a billing account can link to the project. The folder IAM policy can also be
updated with this module.

Typical usage example:

  my_project = project.apply('parent', 'my_id', 'my_displayName', {my_labels})

  project.billing(my_project, 'billing_account')
  project.services(my_project, [services])
  project.control(my_project, {projectPolicy})
"""

from google.cloud.resourcemanager_v3 import (
    Project,
    ProjectsClient,
    CreateProjectRequest,
    SearchProjectsRequest
)
from google.cloud.service_usage_v1 import (
    ServiceUsageClient,
    BatchEnableServicesRequest
)
from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest
from google.cloud.billing_v1 import (
    ProjectBillingInfo,
    CloudBillingClient,
    UpdateProjectBillingInfoRequest
)

def _create(project):
    """Create a project according to a resource declaration.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the declared
            resource.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the project created from
            the operation.
    """
    client = ProjectsClient()
    request = CreateProjectRequest(project=project)

    operation = client.create_project(request=request)
    response = operation.result()

    print('... project created... ')

    return response

def _get(project):
    """Get the existing project corresponding to the declared resource.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            resource.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the existing project if
            it exists.

    Raises:
        IndexError, matching projects amount to 0.
        TypeError, if the matching project is not unique.
    """
    # this is the query to find the matching projects
    query = [
        f'parent={project.parent}',
        'AND state=ACTIVE'
    ]
    for key, value in project.labels.items():
        query.extend([f'AND labels.{key}={value}'])
    query = ' '.join(query)
    # instantiate the list of corresponding projects
    projects = []

    client = ProjectsClient()
    request = SearchProjectsRequest(query=query)

    page_result = client.search_projects(request=request)

    for project in page_result:
        projects.append(project)

    if len(projects) > 1:
        e = TypeError([ project.name for project in projects ])
        raise e

    try:
        project = projects[0]
    except IndexError as exc:
        e = IndexError(0)
        raise e from exc

    return project

def control(project, policy):
    """Apply IAM policy to the project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            resource.
        policy: google.iam.v1.policy_pb2.Policy, the policy to apply.
    """
    client = ProjectsClient()
    request = SetIamPolicyRequest(
        resource=project.name,
        policy=policy
    )

    client.set_iam_policy(request=request)

    return None

def services(project, services_list):
    """Enable a list of services for the project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            resource.
        services: list, a list of services to enable in the project.
    """
    client = ServiceUsageClient()
    request = BatchEnableServicesRequest(
        parent=project.name,
        service_ids=services_list
    )

    operation = client.batch_enable_services(request=request)
    # Waiting loop for the operation to end
    while not operation.done():
        print('... ')

    return None

def billing(project, name):
    """Update billing info for a project

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            resource.
        name: google.cloud.resourcemanager_v3.types.ProjectBillingInfo, the
            declared billing info.

    Returns:
        google.cloud.resourcemanager_v3.types.ProjectBillingInfo, the project
            billing info updated from the operation.
    """
    client = CloudBillingClient()
    request = UpdateProjectBillingInfoRequest(
        name=f'projects/{project.project_id}',
        project_billing_info=ProjectBillingInfo(
            billing_account_name=name
        )
    )

    response = client.update_project_billing_info(request=request)

    return response

def apply(parent, project_id, displayName, labels):
    """Generate a project.
    
    Can either create, update or leave it as it is.

    Args:
        parent: string, the name of the parent hosting the project.
        project_id: string, a unique ID for the project.
        displayName: string, the user-friendly name of the project.
        labels: dict, a map of labels for the project, in a key-value form. 

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the project generated
            according to the declaration.

    Raises:
        TypeError, if the matching project is not unique.
    """
    declared_project = Project(
        parent=parent,
        project_id=project_id,
        display_name=displayName,
        labels=labels
    )

    try:
        existing_project = _get(declared_project)
    except IndexError as e:
        if e.args[0] == 0:
            existing_project = _create(declared_project)
    except TypeError as e:
        print(f'Found {len(e.args[0])} projects')
        print(f'List of projects: {str(e.args[0])}')
        raise e

    return existing_project
