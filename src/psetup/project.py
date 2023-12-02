from random import randint
from google.cloud import resourcemanager_v3
from google.cloud import service_usage_v1
from google.iam.v1 import iam_policy_pb2

def create(project):
    """
    Create a project with google API call.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the project to
            create.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the project created from
            the operation.
    """
    client = resourcemanager_v3.ProjectsClient()
    request = resourcemanager_v3.CreateProjectRequest(project=project)
    operation = client.create_project(request=request)
    response = operation.result()
    return response

def diff(project):
    """
    Show the differences between the declared project and and corresponding
        existing project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            project.

    Returns:
        google.cloud.resourcemanager_v3.types.Project, the matching project if
            it exists.

    Raises:
        ValueError, if there is zero or more than one existing projects
            matching the labels.
    """
    # this is the query to find the matching projects
    query = [
        'parent={0}'.format(project.parent),
        'AND state=ACTIVE'
    ]
    for key, value in project.labels.items():
        query.extend(['AND labels.{0}={1}'.format(key, value)])
    query = ' '.join(query)
    projects = []

    # build the client for resource management
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
        print('ERROR Too many projects with matching labels.')
        e = ValueError(num, [ p.name for p in projects ])
        raise e

def control_access(project, policy):
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

    return None

def enable_services(project, services):
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

    return None

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
    exec_gr = 'group:{0}'.format(setup['google']['groups']['executive_group'])
    labels = setup['rootProject']['labels']
    services = setup['rootProject']['services']
    policy = {'bindings': [{'members': [exec_gr], 'role': 'roles/owner'}]}

    # Construct the declared project
    project = resourcemanager_v3.Project(
        parent=parent,
        project_id=project_id,
        display_name=display_name,
        labels=labels
    )

    try:
        project = diff(project)
        print('project already exists... ', end='')
    except ValueError as e:
        if e.args[0] == 0:
            project = create(project=project)
            print('project created... ', end='')
        else:
            print('Found {0} projects'.format(e.args[0]))
            print('List of projects: {0}'.format(str(e.args[1])))
            raise e
   
    enable_services(project=project, services=services)
    print('services enabled... ', end='')

    control_access(project=project, policy=policy)
    print('IAM policy set... ', end='')

    return project