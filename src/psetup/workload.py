from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operation

class WorkloadIdentityPool:

    def __init__(self, setup, parent):
        self.parent = '{0}/locations/global'.format(parent)
        self.name = '{0}/workloadIdentityPools/{1}'.format(self.parent, setup['organizationPool']['id'])
        self.data = {
            'description': setup['organizationPool']['description'],
            'disabled': 'False',
            'displayName': setup['organizationPool']['id'].replace('-', ' ').title()
        }

    def create(self, credentials):
        """
        Create a workload identity pool with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the pool resulting from the operation.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for iam
        with build('iam', 'v1', credentials=credentials).projects().locations().workloadIdentityPools() as api:
            request = api.create(
                parent=self.parent,
                body=self.data,
                workloadIdentityPoolId=self.name.split('/')[-1]
            )
            try:
                initial = request.execute()
            except HttpError as e:
                raise e
            result = operation.watch(api=api, operation=initial)
        return None

    def update(self, credentials, mask):
        """
        Update a workload identity pool with google API call.

        Args:
            credentials: credential, the user authentification to make a call.
            mask: string, a comma-separated list of fields to update.

        Returns:
            dict, the pool resulting from the operation.
        
        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        with build('iam', 'v1', credentials=credentials).projects().locations().workloadIdentityPools() as api:
            request = api.patch(name=self.name, body=self.data, updateMask=mask)
            try:
                initial = request.execute()
            except HttpError as e:
                raise e
            result = operation.watch(api=api, operation=initial)
        return None

    def diff(self, credentials):
        """
        Show the differences between the declared pool and corresponding
            existing pool.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the difference between declared and existing pools, as a
                dict. If there is no existing state, returns None.
        """
        # build the api for iam
        with build('iam', 'v1', credentials=credentials).projects().locations().workloadIdentityPools() as api:
            request = api.get(name=self.name)
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

class TerraformIdentityProvider:

    def __init__(self, setup, parent):
        self.providerId = setup['terraformProvider']['id']
        self.name = '{0}/providers/{1}'.format(parent, self.providerId)
        self.parent = parent
        self.data =  {  
            'attributeCondition': 'assertion.sub.startsWith("organization:{0}:project:Workspaces")'.format(setup['terraform']['organization']),
            'attributeMapping': setup['terraformProvider']['attributeMapping'],
            'description': setup['terraformProvider']['description'],
            'disabled': False,
            'displayName': setup['terraformProvider']['displayName'],
            'oidc': {
                'allowedAudiences': [
                    'https://tfc.{0}'.format(setup['google']['org_name']),
                ],
                'issuerUri': setup['terraformProvider']['oidc']['issuerUri']
            }
        }

    def create(self, credentials):
        """
        Create a workload identity provider with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the provider resulting from the operation.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for iam
        with build('iam', 'v1', credentials=credentials).projects().locations().workloadIdentityPools().providers() as api:
            request = api.create(
                parent=self.parent,
                body=self.data,
                workloadIdentityPoolProviderId=self.providerId
            )
            try:
                initial = request.execute()
            except HttpError as e:
                raise e
            result = operation.watch(api=api, operation=initial)
        return None
    
    def update(self, credentials, mask):
        """
        Update a workload identity provider with google API call.

        Args:
            credentials: credential, the user authentification to make a call.
            mask: string, a comma-separated list of fields to update.

        Returns:
            dict, the provider resulting from the operation.
        
        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        with build('iam', 'v1', credentials=credentials).projects().locations().workloadIdentityPools().providers() as api:
            request = api.patch(name=self.name, body=self.data, updateMask=mask)
            try:
                initial = request.execute()
            except HttpError as e:
                raise e
            result = operation.watch(api=api, operation=initial)
        return None

    def diff(self, credentials):
        """
        Show the differences between the declared provider and corresponding
            existing proivder.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the difference between declared and existing providers, as a
                dict. If there is no existing state, returns None.
        """
        # build the api for iam
        with build('iam', 'v1', credentials=credentials).projects().locations().workloadIdentityPools().providers() as api:
            request = api.get(name=self.name)
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
        if result['attributeCondition'] != self.data['attributeCondition']:
            diff['attributeCondition'] = self.data['attributeCondition']
        if result['attributeMapping'] != self.data['attributeMapping']:
            diff['attributeMapping'] = self.data['attributeMapping']
        if (result['oidc']['issuerUri'] != self.data['oidc']['issuerUri']) or (result['oidc']['allowedAudiences'] != self.data['oidc']['allowedAudiences']):
            diff['oidc'] = self.data['oidc']
        return diff

def generate_provider(credentials, setup, parent):
    pool = WorkloadIdentityPool(setup=setup, parent=parent)
    diff = pool.diff(credentials=credentials)
    if diff is None:
        pool.create(credentials=credentials)
        print('pool created... ', end='')
    elif diff != {}:
        pool.update(credentials=credentials, mask=','.join(diff.keys()))
        print('pool updated... ', end='')
    provider = TerraformIdentityProvider(setup=setup, parent=pool.name)
    diff = provider.diff(credentials=credentials)
    if diff is None:
        provider.create(credentials=credentials)
        print('provider created... ', end='')
    elif diff != {}:
        provider.update(credentials=credentials, mask=','.join(diff.keys()))
        print('provider updated... ', end='')
    print('provider is up-to-date.')
    return pool