from random import randint
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operation

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
            initial = create_request.execute()
            result = operation.watch(api=api, operation=initial)
        if not 'response' in result:
            raise RuntimeError('the operation result did not contain any response. result: {0}'.format(str(result)))
        self.name = result['response']['name']
        return result['response']

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
        # this is the query to find the matching projects
        query = (
            'parent={0}'.format(self.data['parent']),
            ' AND labels.root=true',
            ' AND state=ACTIVE'
        )
        # build the api for resource management
        projects = []
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            # Look for a project that already matches the declaration
            request = api.projects().search(query=''.join(query))
            while request is not None:
                results = request.execute()
                if 'projects' in results:
                    projects.extend([ p for p in results['projects'] ])
                request = api.projects().search_next(request, results)
        if projects == []:
            return None
        if len(projects) == 1:
            self.name = projects[0]['name']
            self.uuid = projects[0]['projectId']
            self.data['displayName'] = projects[0]['displayName']
            self.data['labels'] = projects[0]['labels']
            self.data['projectId'] = projects[0]['projectId']
            return projects[0]
        if len(projects) > 1:
            raise RuntimeError('There should be at most one project with label root:true in the organization. found: {0}'.format(len(projects)))

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

    def service_enable(self, credentials):
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
                    result.append(operation.watch(api=api, operation=initial)['response']['service']['config']['name'])
                    continue
                result.append(initial['response']['service']['config']['name'])
        return result

def generate_project(credentials, parent, executive_group):
    """
    Generate the root project and related resources.

    Args:
        credentials: credential, the user authentification to make a call.
        parent: string, the name of the organisation hosting the project.
        executive_group: string, the email address of the group for executives
            for the organization.

    Returns:
        RootProject, the project created.
    """
    project = RootProject(
        parent=parent,
        executive_group=executive_group
    )
    diff = project.diff(credentials=credentials)
    if diff is None:
        project.create(credentials=credentials)
        print('project created... ', end='')
    project.service_enable(credentials=credentials)
    print('services enabled... ', end='')
    project.access_control(credentials=credentials)
    print('IAM policies set... ', end='')
    print('project is up-to-date.')
    return project