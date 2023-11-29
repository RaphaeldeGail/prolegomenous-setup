from random import randint
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup.operation import watch
from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2

#from google.cloud import resourcemanager_v3
#client = resourcemanager_v3.FoldersClient()
#folder = resourcemanager_v3.Folder()
#folder.parent = "organizations/66101817749"
#folder.display_name = "toutoutoutou"
#request = resourcemanager_v3.CreateFolderRequest(folder=folder)
#operation = client.create_folder(request=request)
#response = operation.result()
#print(response)

class RootProject:

    def __init__(self, setup):
        self.services = setup['rootProject']['services']

    def enable_services(self, credentials):
        """
        Enable a list of services for the project.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the list of services enabled.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        with build('serviceusage', 'v1', credentials=credentials) as api:
            result = []
            for service in self.services:
                request = api.services().enable(name='{0}/services/{1}'.format(self.name, service))
                try:
                    initial = request.execute()
                except HttpError as e:
                    raise e
                if not ( 'done', True ) in initial.items():
                    result.append(watch(api=api, operation=initial)['service']['config']['name'])
                    continue
                result.append(initial['response']['service']['config']['name'])
        return None

def create(project):
    """
    Create a project with google API call.

    Args:
        credentials: credential, the user authentification to make a call.

    Returns:
        dict, the project resulting from the operation.
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
        credentials: credential, the user authentification to make a call.

    Returns:
        dict, the difference between declared and existing project, as a
            dict. If there is no existing state, returns False.
    """
    # this is the query to find the matching projects
    query = [
        'parent={0}'.format(project.parent),
        'AND state=ACTIVE'
    ]
    client = resourcemanager_v3.ProjectsClient()
    for key, value in project.labels.items():
        query.extend(['AND labels.{0}={1}'.format(key, value)])
    # build the api for resource management
    request = resourcemanager_v3.SearchProjectsRequest(query=' '.join(query))
    page_result = client.search_projects(request=request)
    projects = []
    for project in page_result:
        projects.extend([ project ])
    num = len(projects)
    if num == 0:
        return None
    if num == 1:
        return projects[0]
    if num > 1:
        raise RuntimeError('Found {0} projects with labels'.format(num))

def control_access(project, policy):
    """
    Apply IAM policy to the project.

    Args:
        credentials: credential, the user authentification to make a call.

    Returns:
        dict, the IAM policy applied.

    Raises:
        HttpError, Raises an exception if the API call does not return a
            successful HTTP response.
    """
    client = resourcemanager_v3.ProjectsClient()
    request = iam_policy_pb2.SetIamPolicyRequest(
        resource=project.name,
        policy=policy
    )
    response = client.set_iam_policy(request=request)
    return response

def enable_services(self, credentials):
    """
    Enable a list of services for the project.

    Args:
        credentials: credential, the user authentification to make a call.

    Returns:
        dict, the list of services enabled.

    Raises:
        HttpError, Raises an exception if the API call does not return a
            successful HTTP response.
    """
    with build('serviceusage', 'v1', credentials=credentials) as api:
        result = []
        for service in self.services:
            request = api.services().enable(name='{0}/services/{1}'.format(self.name, service))
            try:
                initial = request.execute()
            except HttpError as e:
                raise e
            if not ( 'done', True ) in initial.items():
                result.append(watch(api=api, operation=initial)['service']['config']['name'])
                continue
            result.append(initial['response']['service']['config']['name'])
    return None


def generate_root(setup):
    """
    Generate the root project and related resources.

    Args:
        credentials: credential, the user authentification to make a call.
        setup: dict, the configuration used to build the root structure.

    Returns:
        RootProject, the root project created.
    """
    display_name = setup['rootProject']['displayName']
    uuid = str(randint(1,999999))
    executive_group = setup['google']['groups']['executive_group']
    labels = setup['rootProject']['labels']
    policy = {
        'bindings': [
            {
                'members': ['group:{0}'.format(executive_group)],
                'role': 'roles/owner'
            }
        ]
    }
    project = resourcemanager_v3.Project(
        parent=setup['parent'],
        project_id='{0}-{1}'.format(display_name, uuid),
        display_name=display_name,
        labels=labels
    )
    delta = diff(project)
    if delta is None:
        project = create(project=project)
        print('project created... ', end='')
    else:
        project = delta

    # project.enable_services(credentials=credentials)
    # print('services enabled... ', end='')
    control_access(project=project, policy=policy)
    print('IAM policy set... ', end='')
    return project