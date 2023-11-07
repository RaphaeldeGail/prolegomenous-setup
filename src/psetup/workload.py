from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operations

class WorkloadIdentityPool:

    poolId = 'organization-identity-pool'

    def __init__(self, parent):
        self.name = '{0}/locations/global/workloadIdentityPools/{1}'.format(parent, self.poolId)
        self.parent = parent
        self.data = {
            'description': '',
            'disabled': 'False',
            'displayName': self.poolId.replace('-', ' ').title()
        }

    def create(self, credentials):
        """
        Create a workload identity pool with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the pool resulting from the operation.
        """
        # build the api for iam
        with build('iam', 'v1', credentials=credentials).projects().locations() as api:
            request = api.workloadIdentityPools().create(
                parent=self.parent,
                body=self.data,
                workloadIdentityPoolId=self.poolId
            )
            operation = request.execute()
            pool = operations.watch(api=api, name=operation['name'])
        self.name = pool['name']
        return pool

    def diff(self, credentials):
        """
        Show the differences between the declared pool and and corresponding
            existing pool.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the difference between declared and existing pools, as a
                dict. If there is no existing state, returns False.
        """
        # build the api for iam
        with build('iam', 'v1', credentials=credentials).projects().locations() as api:
            request = api.workloadIdentityPools().get(name=self.name)
            try:
                result = request.execute()
            except HttpError as e:
                if e.status_code != 404:
                    raise e
                return None
        diff = {}
        if result['description'] != self.data['description']:
            diff['description'] = self.data['description']
        if result['state'] != 'ACTIVE':
            diff['disabled'] = self.data['disabled']
        if result['displayName'] != self.data['displayName']:
            diff['displayName'] = self.data['displayName']        
        return diff
    
def generate_pool(credentials, parent):
    pool = WorkloadIdentityPool(parent=parent)
    #diff = pool.diff(credentials=credentials)
    return pool