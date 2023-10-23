from random import randint
from googleapiclient.discovery import build
from time import sleep

class RootProject:

    def __init__(self, parent, executive_group, name):
        name= self.name
        self.uuid = randint(1,999999)
        self.project = {
            'displayName': name,
            'labels': {
                'root': 'true',
                'uuid': str(self.uuid)
            },
            'parent': parent,
            'projectId': '{ name }-{ str(uuid) }'.format(name=name, uuid=self.uuid)
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

    def apply(self, credentials, timeout=60):
        """
        Create a project with google API call.

        Args:
            credentials: credential, the user authentification to make a call.
            timeout: int, the timeout before project creation fails,
                in seconds. defaults to 60 seconds.

        Returns:
            dict, the project resulting from the operation.

        Raises:
            RuntimeError: Raises an exception if the API call does not return a
                successful response.
        """
        # build the api for resource management
        api = build('cloudresourcemanager', 'v3', credentials=credentials)
        # the period is the number, in seconds, between two consecutive checks
        period = 5
        # error message if creation status times out
        status_timeout = 'timeout before project creation status is available.'
        # error message if creation completion times out
        completion_timeout = 'timeout before project creation is done.'
        create_request = api.projects().create(body=self.project)
        operation = create_request.execute()

        operation_request = api.operations().get(name=operation['name'])

        # this loop will check for updates every 5 seconds during 1 minute.
        time_elapsed = 0
        operation = operation_request.execute()
        while not 'done' in operation:
            if time_elapsed > timeout % period :
                raise RuntimeError(status_timeout)
            time_elapsed += 1
            sleep(period)
            operation = operation_request.execute()

        # this loop will check for updates every 5 seconds during 1 minute.
        time_elapsed = 0
        while operation['done'] is False:
            if time_elapsed > timeout % period :
                raise RuntimeError(completion_timeout)
            time_elapsed += 1
            sleep(period)
            operation = operation_request.execute()

        api.close()
        return operation['response']

    def diff(self, credentials):
        """
        Show the differences between the declared project and and corresponding
            existing project.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the difference between declared and existing project, as a
                dict. If there is no existing state, returns False.

        Raises:
            RuntimeError: Raises an exception if the API call does not return a
                successful response.
        """
        # build the api for resource management
        api = build('cloudresourcemanager', 'v3', credentials=credentials)
        declared = self.project
        # Look for a project that already matches the declaration
        # this is the query to find the project
        query = 'displayName={name} AND parent={parent} AND labels.root=true \
AND labels.uuid:* AND projectId:{name}-*'.format(parent=declared['parent'], name=self.name)
        request = api.projects().search(query=query)
        result_projects = request.execute()
        if not 'projects' in result_projects:
            api.close()
            return False
        existing = result_projects['projects'][0]
        diff = {}
        if declared['projectId'] != existing['projectId']:
            diff['projectId'] = existing['projectId']
        if declared['labels']['uuid'] != existing['labels']['uuid']:
            diff['labels']['uuid'] = existing['labels']['uuid']
        api.close()
        return diff


def check_project(credentials, parent, executive_group, name='root'):
    project = RootProject(parent=parent, executive_group=executive_group, name=name)



    return project().diff(credentials=credentials)