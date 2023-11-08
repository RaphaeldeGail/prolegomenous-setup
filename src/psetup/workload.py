from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operations

class WorkloadIdentityPool:

    poolId = 'organization-identity-pool'

    def __init__(self, parent):
        self.name = '{0}/locations/global/workloadIdentityPools/{1}'.format(parent, self.poolId)
        self.parent = parent
        self.data = {
            'description': 'This pool provides identities with organization scopes.',
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
        with build('iam', 'v1', credentials=credentials).projects().locations().workloadIdentityPools() as api:
            request = api.create(
                parent=self.parent,
                body=self.data,
                workloadIdentityPoolId=self.poolId
            )
            try:
                operation = request.execute()
            except HttpError as e:
                raise e
            pool = operations.watch(api=api, name=operation['name'])
        self.name = pool['name']
        return pool

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
                operation = request.execute()
            except HttpError as e:
                raise e
            if ( not 'name' in operation ) and ( 'done' in operation ):
                return operation['response']
            pool = operations.watch(api=api, name=operation['name'])
        return pool

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

    providerId = 'tfc-oidc'

    def __init__(self, parent, terraform_org, org_name):
        self.name = '{0}/providers/{1}'.format(parent, self.providerId)
        self.parent = parent
        self.data =  {  
            'attributeCondition': 'assertion.sub.startsWith("organization:{0}:project:Workspaces")'.format(terraform_org),
            'attributeMapping': {
                'attribute.aud': 'assertion.aud',
                'attribute.terraform_full_workspace': 'assertion.terraform_full_workspace',
                'attribute.terraform_organization_id': 'assertion.terraform_organization_id',
                'attribute.terraform_organization_name': 'assertion.terraform_organization_name',
                'attribute.terraform_project_id': 'assertion.terraform_project_id',
                'attribute.terraform_project_name': 'assertion.terraform_project_name',
                'attribute.terraform_run_id': 'assertion.terraform_run_id',
                'attribute.terraform_run_phase': 'assertion.terraform_run_phase',
                'attribute.terraform_workspace_id': 'assertion.terraform_workspace_id',
                'attribute.terraform_workspace_name': 'assertion.terraform_workspace_name',
                'google.subject': 'assertion.sub'
            },
            'description': 'Terraform Cloud identity provider.',
            'disabled': False,
            'displayName': 'Terraform Cloud OIDC Provider',
            'oidc': {
                'allowedAudiences': [
                    'https://tfc.{0}'.format(org_name),
                ],
                'issuerUri': 'https://app.terraform.io'
            }
        }

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
        return diff

def generate_pool(credentials, parent):
    pool = WorkloadIdentityPool(parent=parent)
    diff = pool.diff(credentials=credentials)
    if diff is None:
        pool.create(credentials=credentials)
        print('pool created... ', end='')
    elif diff != {}:
        pool.update(credentials=credentials, mask=','.join(diff.keys()))
        print('pool updated... ', end='')
    print('pool is up-to-date.')
    provider = TerraformIdentityProvider(parent=pool.name, terraform_org='yo', org_name='yo')
    diff = provider.diff(credentials=credentials)
    print(diff)
    return pool