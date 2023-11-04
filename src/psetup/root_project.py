from random import randint
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operations

class RootProject:

    display_name = 'root'

    def __init__(self, parent, executive_group):
        self.name = None
        self.uuid = randint(1,999999)
        self.data = {
            'displayName': self.display_name,
            'labels': {
                'root': 'true',
                'uuid': str(self.uuid)
            },
            'parent': parent,
            'projectId': '{name}-{uuid}'.format(name=self.display_name, uuid=str(self.uuid))
        }
        self.services = [
            'cloudapis.googleapis.com',
            'cloudbilling.googleapis.com',
            'cloudidentity.googleapis.com',
            'cloudkms.googleapis.com',
            'cloudresourcemanager.googleapis.com',
            'cloudtrace.googleapis.com',
            'datastore.googleapis.com',
            'iam.googleapis.com',
            'iamcredentials.googleapis.com',
            'logging.googleapis.com',
            'servicemanagement.googleapis.com',
            'serviceusage.googleapis.com',
            'storage-api.googleapis.com',
            'storage-component.googleapis.com',
            'storage.googleapis.com',
            'sts.googleapis.com',
            'secretmanager.googleapis.com',
            'billingbudgets.googleapis.com',
            'dns.googleapis.com'
        ]
        self.iam_bindings = {
            'policy': {
                'bindings': [
                    {
                        'members': ['group:{0}'.format(executive_group)],
                        'role': 'roles/owner'
                    }
                ]
            }
        }

    def create(self, credentials):
        """
        Create a project with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the project resulting from the operation.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            create_request = api.projects().create(body=self.data)
            operation = create_request.execute()
            project = operations.watch(api=api, name=operation['name'])
        self.name = project['name']
        return project

    def update(self, credentials):
        """
        Update a project with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the project resulting from the operation.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            update_request = api.projects().patch(name=self.name, body=self.data)
            operation = update_request.execute()
            project = operations.watch(api=api, name=operation['name'])
        return project

    def diff(self, credentials):
        """
        Show the differences between the declared project and and corresponding
            existing project.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the difference between declared and existing project, as a
                dict. If there is no existing state, returns False.
        """
        # this is the query to find the project
        query = 'parent={0} AND labels.root=true AND state=ACTIVE'.format(self.data['parent'])
        #' AND displayName={0}'.format(self.display_name),
        #' AND labels.uuid:*',
        #' AND projectId:{0}-*'.format(self.display_name)
        # build the api for resource management
        p_list = []
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            # Look for a project that already matches the declaration
            request = api.projects().search(query=query)
            while request is not None:
                result_projects = request.execute()
                if 'projects' in result_projects:
                    for p in result_projects['projects']:
                        p_list.append(p)
                request = api.projects().search_next(request, result_projects)
        if p_list == []:
            return None
        if len(p_list) == 1:
            self.name = p_list[0]['name']
            self.uuid = p_list[0]['projectId']
            self.data['displayName'] = p_list[0]['displayName']
            self.data['labels'] = p_list[0]['displayName']
            self.data['projectId'] = p_list[0]['projectId']
            return p_list[0]
        if len(p_list) > 1:
            print('clear')  
            return None

    def access_control(self, credentials):
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
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            request = api.projects().setIamPolicy(resource=self.name, body=self.iam_bindings)
            try:
                result_policy = request.execute()
            except HttpError as e:
                raise e
        return result_policy

def generate_project(credentials, parent, executive_group):
    """
    Generate the root project and related resources.

    Args:
        credentials: credential, the user authentification to make a call.
        parent: string, the name of the organisation hosting the project.
        executive_group: string, the email address of the group for executives
            for the organization.
        uuid: int, a unique uid for the root project. Defaults to a random
            integer between 1 and 999999.

    Returns:
        RootProject, the project created.
    """
    project = RootProject(
        parent=parent,
        executive_group=executive_group
    )
    diff = project.diff(credentials=credentials)
    if diff is None:
        project.apply(credentials=credentials)
        print('project created... ', end='')
    project.access_control(credentials=credentials)
    print('project is up-to-date... ', end='')
    return project