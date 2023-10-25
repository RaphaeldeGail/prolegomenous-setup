from random import randint
from googleapiclient.discovery import build
from psetup import operations

class RootProject:

    display_name = 'root'

    def __init__(self, parent, executive_group, uuid):
        self.name = None
        self.uuid = uuid
        self.project = {
            'displayName': self.display_name,
            'labels': {
                'root': 'true',
                'uuid': str(uuid)
            },
            'parent': parent,
            'projectId': '{name}-{uuid}'.format(name=self.display_name, uuid=str(uuid))
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
            'members': [
                {
                    'group': executive_group,
                    'role': 'roles/owner'
                }
            ]
        }

    def apply(self, credentials):
        """
        Create a project with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the project resulting from the operation.
        """
        # build the api for resource management
        api = build('cloudresourcemanager', 'v3', credentials=credentials)
        create_request = api.projects().create(body=self.project)
        operation = create_request.execute()
        project = operations.watch(api=api, name=operation['name'])
        api.close()
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
        api = build('cloudresourcemanager', 'v3', credentials=credentials)
        update_request = api.projects().patch(name=self.name, body=self.project)
        operation = update_request.execute()
        project = operations.watch(api=api, name=operation['name'])
        api.close()
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
        # build the api for resource management
        api = build('cloudresourcemanager', 'v3', credentials=credentials)
        declared = self.project
        # Look for a project that already matches the declaration
        # this is the query to find the project
        query = 'displayName={name} AND parent={parent} AND labels.root=true AND labels.uuid:* AND projectId:{name}-*'.format(parent=declared['parent'], name=self.display_name)
        request = api.projects().search(query=query)
        result_projects = request.execute()
        if not 'projects' in result_projects:
            api.close()
            return False
        for p in result_projects['projects']:
            if p['projectId'] == self.project['projectId']:
                self.name = p['name']
                if p['labels']['uuid'] == self.project['labels']['uuid']:
                    return {}
                return { 'labels': p['labels']['uuid'] }
        return False

def check_project(credentials, parent, executive_group, uuid=randint(1,999999)):
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
        the project data and name.
    """
    project = RootProject(
        parent=parent,
        executive_group=executive_group,
        uuid=uuid
    )
    diff = project.diff(credentials=credentials)
    if diff is False:
        project.apply(credentials=credentials)
        print('project created... ', end='')
        return project.project, project.name
    if diff != {}:
        print('project updated... ', end='')
        project.update(credentials=credentials)
        return project.project, project.name
    print('project is up-to-date... ', end='')
    return project.project, project.name