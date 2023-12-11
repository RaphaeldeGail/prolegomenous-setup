from random import randint
from google.cloud import resourcemanager_v3
from google.cloud import service_usage_v1
from google.iam.v1 import iam_policy_pb2
from google.cloud import billing_v1

def _create_project(project):
    """
    Create a project according to a declared project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the declared
            project.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the project created from
            the operation.
    """
    client = resourcemanager_v3.ProjectsClient()
    request = resourcemanager_v3.CreateProjectRequest(project=project)

    operation = client.create_project(request=request)
    response = operation.result()

    print('project created... ', end='')

    return response

def _get_project(project):
    """
    Get the existing project in Google organization corresponding to the
        declared project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            project.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the existing project if
            it is unique.

    Raises:
        ValueError, if there is no project matching the declared project, or if
        the matching project is not unique.
    """
    # this is the query to find the matching projects
    query = [
        'parent={0}'.format(project.parent),
        'AND state=ACTIVE'
    ]
    for key, value in project.labels.items():
        query.extend(['AND labels.{0}={1}'.format(key, value)])
    query = ' '.join(query)
    # instantiate the list of corresponding projects
    projects = []

    client = resourcemanager_v3.ProjectsClient()
    request = resourcemanager_v3.SearchProjectsRequest(query=query)

    page_result = client.search_projects(request=request)

    for project in page_result:
        projects.append(project)
    
    num = len(projects)

    if num == 0:
        e = ValueError(num)
        raise e

    if num == 1:
        return projects[0]

    if num > 1:
        e = ValueError(num, [ p.name for p in projects ])
        raise e

def _control_access(project, policy):
    """
    Apply IAM policy to the project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            project.
        policy: dict, list all `bindings` to apply to the project policy.
    """
    client = resourcemanager_v3.ProjectsClient()
    request = iam_policy_pb2.SetIamPolicyRequest(
        resource=project.name,
        policy=policy
    )

    client.set_iam_policy(request=request)

    print('IAM policy set... ', end='')

    return None

def _enable_services(project, services):
    """
    Enable a list of services for the project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            project.
        services: list, a list of services to enable in the project.
    """
    client = service_usage_v1.ServiceUsageClient()
    request = service_usage_v1.BatchEnableServicesRequest(
        parent=project.name,
        service_ids=services 
    )

    operation = client.batch_enable_services(request=request)
    operation.result()

    print('services enabled... ', end='')

    return None

def _update_billing(billing):
    """
    Update a project billing info compared to a declared value.

    Args:
        billing: google.cloud.resourcemanager_v3.types.ProjectBillingInfo, the
            declared project billing info.

    Returns:
        google.cloud.resourcemanager_v3.types.ProjectBillingInfo, the project
            billing info updated from the operation.
    """
    client = billing_v1.CloudBillingClient()
    request = billing_v1.UpdateProjectBillingInfoRequest(
        name='projects/{0}'.format(billing.project_id),
        project_billing_info=billing
    )

    response = client.update_project_billing_info(request=request)

    print('billing enabled... ', end='')
    
    return response

def generate_root(setup):
    """
    Generate the root project and related resources. Can either create, update
        or leave it as it is. The project is also updated with a list of
        services enabled and a new IAM policy.

    Args:
        setup: dict, the configuration used to build the root structure.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the generated project.
    """
    # Sets the variables for generating the project
    parent = setup['parent']
    display_name = setup['rootProject']['displayName']
    uuid = str(randint(1,999999))
    project_id = '{0}-{1}'.format(display_name, uuid)
    exec_grp = 'group:{0}'.format(setup['google']['groups']['executive_group'])
    labels = setup['rootProject']['labels']
    services = setup['rootProject']['services']
    bill = 'billingAccounts/{0}'.format(setup['google']['billing_account'])
    policy = {'bindings': [{'members': [exec_grp], 'role': 'roles/owner'}]}

    declared_project = resourcemanager_v3.Project(
        parent=parent,
        project_id=project_id,
        display_name=display_name,
        labels=labels
    )

    declared_billing = billing_v1.ProjectBillingInfo(
        billing_account_name=bill
    )

    try:
        project = _get_project(declared_project)
    except ValueError as e:
        if e.args[0] == 0:
            project = _create_project(declared_project)
        else:
            print('Found {0} projects'.format(e.args[0]))
            print('List of projects: {0}'.format(str(e.args[1])))
            raise e
    
    declared_billing.project_id = project.project_id

    _update_billing(declared_billing)
   
    _enable_services(project=project, services=services)

    _control_access(project=project, policy=policy)

    return project