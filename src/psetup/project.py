"""Generate a root project idempotently.

Can apply a specific configuration for a root project and create or update it
in order to match the configuration.

Typical usage example:

  root_project = generate_root(setup)
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

def _create_project(project):
    """Create a project according to a declared project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the declared
            project.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the project created by
            the operation.
    """
    client = ProjectsClient()
    request = CreateProjectRequest(project=project)

    operation = client.create_project(request=request)
    response = operation.result()

    print('project created... ', end='')

    return response

def _get_project(project):
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

def control_access(project, policy):
    """Apply IAM policy to the project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            project.
        policy: dict, list all `bindings` to apply to the project policy.
    """
    client = ProjectsClient()
    request = SetIamPolicyRequest(
        resource=project.name,
        policy=policy.format
    )

    client.set_iam_policy(request=request)

    return None

def enable_services(project, services):
    """Enable a list of services for the project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            project.
        services: list, a list of services to enable in the project.
    """
    client = ServiceUsageClient()
    request = BatchEnableServicesRequest(
        parent=project.name,
        service_ids=services
    )

    operation = client.batch_enable_services(request=request)
    operation.result()

    return None

def update_billing(project, name):
    """Update a project billing info compared to a declared value.

    Args:
        billing: google.cloud.resourcemanager_v3.types.ProjectBillingInfo, the
            declared project billing info.

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

def apply_project(parent, id, displayName, labels):
    """Apply the declared project to the Google Cloud organization.
    
    Can either create, update or leave it as it is.

    Args:
        declared_project: google.cloud.resourcemanager_v3.types.Project, the
            project as declared.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the project resulting
            from the operation.

    Raises:
        TypeError, if the matching project is not unique.
    """
    declared_project = Project(
        parent=parent,
        project_id=id,
        display_name=displayName,
        labels=labels
    )

    try:
        existing_project = _get_project(declared_project)
    except IndexError as e:
        if e.args[0] == 0:
            existing_project = _create_project(declared_project)
    except TypeError as e:
        print(f'Found {len(e.args[0])} projects')
        print(f'List of projects: {str(e.args[0])}')
        raise e

    return existing_project

def project_info(declared_project):
    """Look for infos of the declared.

    Args:
        declared_project: google.cloud.resourcemanager_v3.types.Project, the
            project as declared.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the matching project.

    Raises:
        ValueError, if the declared project is empty.
        IndexError, if there is no project matching the declared project.
        TypeError, if the matching project is not unique.
    """
    project_id = declared_project.project_id
    display_name = declared_project.display_name
    labels = declared_project.labels

    if not (project_id and display_name and labels):
        print('At least one of project_id, display_name or labels should be')
        raise ValueError('Query is empty')

    try:
        project = _get_project(declared_project)
    except IndexError as e:
        if e.args[0] == 0:
            print('Project not found')
            raise e
    except TypeError as e:
        print(f'Found {len(e.args[0])} projects')
        print(f'List of projects: {str(e.args[0])}')
        raise e

    return project
