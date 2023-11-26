from random import randint
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operation

class RootProject:

    def __init__(self, setup):
        display_name = setup['rootProject']['displayName']
        executive_group = setup['google']['groups']['executive_group']
        self.labels = setup['rootProject']['labels']
        self.name = None
        self.uuid = str(randint(1,999999))
        self.data = {
            'displayName': display_name,
            'labels': self.labels,
            'parent': setup['parent'],
            'projectId': '{0}-{1}'.format(display_name, self.uuid)
        }
        self.services = setup['rootProject']['services']
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
            request = api.projects().create(body=self.data)
            initial = request.execute()
            result = operation.watch(api=api, operation=initial)
        if not 'name' in result:
            raise RuntimeError('No name found in: {0}'.format(str(result)))
        self.name = result['name']
        return None

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
        query = [
            'parent={0}'.format(self.data['parent']),
            ' AND state=ACTIVE'
        ]
        query.extend([' AND labels.{0}={1}'.format(key, value) for key, value in self.labels.items()])
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
            raise RuntimeError('Found {0} projects with labels'.format(len(projects)))

    def control_access(self, credentials):
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
        return None

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
                    result.append(operation.watch(api=api, operation=initial)['service']['config']['name'])
                    continue
                result.append(initial['response']['service']['config']['name'])
        return None

def generate_root(credentials, setup):
    """
    Generate the root project and related resources.

    Args:
        credentials: credential, the user authentification to make a call.
        setup: dict, the configuration used to build the root structure.

    Returns:
        RootProject, the root project created.
    """
    project = RootProject(
        setup=setup
    )
    diff = project.diff(credentials=credentials)
    if diff is None:
        project.create(credentials=credentials)
        print('project created... ', end='')
    project.enable_services(credentials=credentials)
    print('services enabled... ', end='')
    project.control_access(credentials=credentials)
    print('IAM policies set... ', end='')
    return project