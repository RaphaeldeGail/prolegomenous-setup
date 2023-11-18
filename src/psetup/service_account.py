from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class ServiceAccount:

    def __init__(self, setup, parent, poolId):
        self.name = 'projects/{projectId}/serviceAccounts/{name}@{projectId}.iam.gserviceaccount.com'.format(projectId=parent, name=setup['builderAccount']['name'])
        self.data = { 
            'description': setup['builderAccount']['description'],
            'displayName': setup['builderAccount']['displayName']
        }
        self.iam_bindings = {
            'policy': {
                'bindings': [
                    {
                        'members': [
                            'group:{0}'.format(setup['google']['groups']['executive_group']),
                        ],
                        'role': 'roles/iam.serviceAccountTokenCreator',
                    },
                    {
                        'members': [
                            'principalSet://iam.googleapis.com/{0}/attribute.terraform_project_id/{1}'.format(poolId, setup['terraform']['workspace_project']),
                        ],
                        'role': 'roles/iam.workloadIdentityUser',
                    },
                ],
            },
        }
    
    def create(self, credentials):
        """
        Create a service account with google API call.

        Args:
            credentials: credentials, the user authentification to make a call.

        Returns:
            dict, the service account resulting from the operation.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        body = {
            'accountId': 'builder',
            'serviceAccount': self.data
        }
        with build('iam', 'v1', credentials=credentials).projects().serviceAccounts() as api:
            request = api.create(name=self.name.split('/serviceAccounts/')[0], body=body)
            try:
                service_account = request.execute()
            except HttpError as e:
                raise e
        return service_account
    
    def update(self, credentials, mask):
        """
        Update a service account with google API call.

        Args:
            credentials: credential, the user authentification to make a call.
            mask: string, a comma-separated list of fields to update.

        Returns:
            dict, the service account resulting from the operation.
        
        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        body = {
            'serviceAccount': self.data,
            'updateMask': mask
        }
        with build('iam', 'v1', credentials=credentials).projects().serviceAccounts() as api:
            request = api.patch(name=self.name, body=body)
            try:
                service_account = request.execute()
            except HttpError as e:
                raise e
        return service_account
    
    def diff(self, credentials):
        """
        Show the differences between the declared service account and
            corresponding existing one.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the difference between declared and existing service account,
                as a dict. If there is no existing state, returns None.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        with build('iam', 'v1', credentials=credentials).projects().serviceAccounts() as api:
            request = api.get(name=self.name)
            try:
                service_account = request.execute()
            except HttpError as e:
                if e.status_code == 403:
                    return None
                raise e
        diff = {}
        if service_account['description'] != self.data['description']:
            diff['description'] = self.data['description']
        if service_account['displayName'] != self.data['displayName']:
            diff['displayName'] = self.data['displayName']
        return diff
    
    def access_control(self, credentials):
        """
        Apply IAM policy to the service account.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the IAM policy applied.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        with build('iam', 'v1', credentials=credentials).projects().serviceAccounts() as api:
            request = api.setIamPolicy(resource=self.name, body=self.iam_bindings)
            try:
                result = request.execute()
            except HttpError as e:
                raise e
        return None

def generate_service_account(credentials, setup, parent, poolId):
    service_account = ServiceAccount(setup=setup, parent=parent, poolId=poolId)
    diff = service_account.diff(credentials=credentials)
    if diff is None:
        service_account.create(credentials=credentials)
        print('service account created... ', end='')
    elif diff != {}:
        service_account.update(credentials=credentials, mask=','.join(diff.keys()))
        print('service account updated... ', end='')
    service_account.access_control(credentials=credentials)
    print('service_account is up-to-date.')
    return service_account