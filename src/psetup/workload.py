from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operation
from google.cloud import iam_v2
from google.protobuf import field_mask_pb2

class WorkloadIdentityPool:

    def __init__(self, name=None, display_name=None, description=None):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.disabled = False

    def from_dict(self, body):
        try:
            self.name = body['name']
        except KeyError:
            pass
        try:
            self.description = body['description']
        except KeyError:
            pass
        try:
            self.display_name = body['displayName']
        except KeyError:
            pass

    @property
    def id(self):
        id = self.name.split('/')[-1]
        return id

    @property
    def parent(self):
        parent = self.name.split('/workloadIdentityPools/')[0]
        return parent

class WorkloadIdentityProvider:

    def __init__(self, name=None, attribute_condition=None, attribute_mapping=None, description=None, display_name=None, oidc=None):
        self.name = name
        self.attribute_condition = attribute_condition
        self.attribute_mapping = attribute_mapping
        self.description = description
        self.disabled = False
        self.display_name = display_name
        self.oidc = oidc

    def from_dict(self, body):
        try:
            self.name = body['name']
        except KeyError:
            pass
        try:
            self.description = body['description']
        except KeyError:
            pass
        self.disabled = False
        try:
            self.display_name = body['displayName']
        except KeyError:
            pass
        try:
            self.attribute_condition = body['attributeCondition']
        except KeyError:
            pass
        try:
            self.attribute_mapping = body['attributeMapping']
        except KeyError:
            pass
        try:
            self.oidc = body['oidc']
        except KeyError:
            pass
    @property
    def id(self):
        id = self.name.split('/')[-1]
        return id
    
    @property
    def parent(self):
        parent = self.name.split('/providers/')[0]
        return parent

def _create_pool(pool):
    """
    Create a workload identity pool according to a declared one.

    Args:
        pool: WorkloadIdentityPool, the delcared workload identity pool.

    Returns:
        WorkloadIdentityPool, the workload identity pool created from the
            operation.
    """
    # build the create request body
    body = {
        'description': pool.description,
        'disabled': pool.disabled,
        'displayName': pool.display_name
    }

    existing_pool = WorkloadIdentityPool(
        name=pool.name
    )

    client = ('iam', 'v1').projects().locations().workloadIdentityPools()

    with client as api:
        request = api.create(
            parent=pool.parent,
            body=body,
            workloadIdentityPoolId=pool.id
        )

        initial = request.execute()
        result = operation.watch(api=api, operation=initial)

    existing_pool.from_dict(result)

    print('pool created... ', end='')

    return existing_pool

def _update_pool(declared_pool, existing_pool):
    """
    Update an existing workload identity pool compared to a declared one.

    Args:
        declared_pool: WorkloadIdentityPool, the declared workload identity
            pool.
        existing_pool: WorkloadIdentityPool, the existing workload identity
            pool.

    Returns:
        WorkloadIdentityPool, the workload identity pool updated from the
            operation.
    """
    mask = _diff_pool(declared=declared_pool, existing=existing_pool)
    # build the create request body
    body = {
        'description': declared_pool.description,
        'disabled': declared_pool.disabled,
        'displayName': declared_pool.display_name
    }

    # If there is non differences, return the original existing key.
    if mask == []:
        return existing_pool

    client = build('iam', 'v1').projects().locations().workloadIdentityPools() 
    
    with client as api:
        request = api.patch(
            name=declared_pool.name,
            body=body,
            updateMask=','.join(mask)
        )

        initial = request.execute()
        result = operation.watch(api=api, operation=initial)

    existing_pool.from_dict(result)

    print('pool updated... ', end='')

    return existing_pool

def _get_pool(pool):
    """
    Get the existing workload identity pool in project corresponding to the
        declared workload identity pool.

    Args:
        pool: WorkloadIdentityPool, the delcared workload identity pool.

    Returns:
        WorkloadIdentityPool, the existing workload identity pool.

    Raises:
        ValueError, if there is no workload identity pool matching the
            definition.
    """
    parent = pool.parent
    existing = None

    existing_pool = WorkloadIdentityPool(
        name=pool.name
    )

    client = build('iam', 'v1').projects().locations().workloadIdentityPools()

    with client as api:
        request = api.list(parent=parent)

        while request is not None:
            results = request.execute()
            
            for result in results['workloadIdentityPools']:
                if result['name'] == pool.name:
                    existing = result

            request = api.list_next(request, results)
    
    if existing is None:
        raise ValueError(0)
    
    existing_pool.from_dict(existing)

    return existing_pool

def _diff_pool(declared, existing):
    """
    Show the differences between a declared and an existing workload identity
        pool.

    Args:
        declared: WorkloadIdentityPool, the delcared workload identity pool.
        existing: WorkloadIdentityPool, the existing workload identity pool.

    Returns:
        list, the list of attributes to update to match existing and declared.
    """
    mask = []

    if existing.name != declared.name:
        mask.append('name')
    if existing.description != declared.description:
        mask.append('description')
    if existing.display_name != declared.display_name:
        mask.append('displayName')
    
    return mask

def _get_provider(provider):
    """
    Get the existing workload identity provider in project corresponding to the
        declared workload identity provider.

    Args:
        provider: WorkloadIdentityProvider, the delcared workload identity
            provider.

    Returns:
        WorkloadIdentityProvider, the existing workload identity provider.

    Raises:
        ValueError, if there is no workload identity provider matching the
            definition.
    """
    parent = provider.parent
    existing = None

    existing_provider = WorkloadIdentityProvider(
        name=provider.name
    )

    client = build('iam', 'v1').projects().locations().workloadIdentityPools().providers()

    with client as api:
        request = api.list(parent=parent)

        while request is not None:
            results = request.execute()
            
            for result in results['workloadIdentityPoolProviders']:
                if result['name'] == provider.name:
                    existing = result

            request = api.list_next(request, results)
    
    if existing is None:
        raise ValueError(0)
    
    existing_provider.from_dict(existing)

    return existing_provider

def _update_provider(declared_provider, existing_provider):
    """
    Update an existing workload identity provider compared to a declared one.

    Args:
        declared_provider: WorkloadIdentityProvider, the declared workload
            identity provider.
        existing_provider: WorkloadIdentityProvider, the existing workload
            identity provider.

    Returns:
        WorkloadIdentityProvider, the workload identity provider updated from
            the operation.
    """
    mask = _diff_provider(declared_provider, existing_provider)
    # build the create request body
    body = {
        'description': declared_provider.description,
        'disabled': declared_provider.disabled,
        'displayName': declared_provider.display_name,
        'attributeCondition': declared_provider.attribute_condition,
        'attributeMapping': declared_provider.attribute_mapping,
        'oidc': declared_provider.oidc
    }

    # If there is non differences, return the original existing key.
    if mask == []:
        return 
        
    client = build('iam', 'v1').projects().locations().workloadIdentityPools().providers()
    
    with client as api:
        request = api.patch(
            name=declared_provider.name,
            body=body,
            updateMask=','.join(mask)
        )

        initial = request.execute()
        result = operation.watch(api=api, operation=initial)

    existing_provider.from_dict(result)

    print('provider updated... ', end='')

    return existing_provider

def _diff_provider(declared, existing):
    """
    Show the differences between a declared and an existing workload identity
        provider.

    Args:
        declared: WorkloadIdentityProvider, the delcared workload identity
            provider.
        existing: WorkloadIdentityProvider, the existing workload identity
            provider.

    Returns:
        list, the list of attributes to update to match existing and declared.
    """
    mask = []

    if existing.name != declared.name:
        mask.append('name')
    if existing.description != declared.description:
        mask.append('description')
    if existing.display_name != declared.display_name:
        mask.append('displayName')
    if existing.attribute_condition != declared.attribute_condition:
        mask.append('attritubteCondition')
    if existing.attribute_mapping != declared.attribute_mapping:
        mask.append('attritubteMapping')    
    if existing.oidc != declared.oidc:
        mask.append('oidc')
    
    return mask

def _create_provider(provider):
    """
    Create a workload identity provider according to a declared one.

    Args:
        provider: WorkloadIdentityProvider, the delcared workload identity
            provider.

    Returns:
        WorkloadIdentityProvider, the workload identity provider created from
            the operation.
    """
    # build the create request body
    body = {
        'description': provider.description,
        'disabled': provider.disabled,
        'displayName': provider.display_name,
        'attributeCondition': provider.attribute_condition,
        'attributeMapping': provider.attribute_mapping,
        'oidc': provider.oidc
    }
    existing_provider = WorkloadIdentityPool(
        name=provider.name
    )

    client = build('iam', 'v1').projects().locations().workloadIdentityPools().providers()

    with client as api:
        request = api.create(
            parent=provider.parent,
            body=body,
            workloadIdentityPoolProviderId=provider.id
        )

        initial = request.execute()
        result = operation.watch(api=api, operation=initial)

    existing_provider.from_dict(result)

    print('provider created... ', end='')

    return existing_provider

def generate_terraform_provider(setup, project):
    """
    Generate the workload identity pool and identity provider for terraform.
        Can either create, update or leave it as it is.

    Args:
        setup: dict, the configuration used to build the root structure.
        project: string, the name of the project hosting the workload identity
            pool.

    Returns:
        WorkloadIdentityPool, the generated workload identity pool.
    """
    terraform_org = setup['terraform']['organization']
    org_name = setup['google']['org_name']

    declared_pool = WorkloadIdentityPool(
        name='{0}/locations/global/workloadIdentityPools/{1}'.format(project,setup['organizationPool']['id']),
        description=setup['organizationPool']['description'],
        display_name=setup['organizationPool']['id'].replace('-', ' ').title()
    )
    declared_provider = WorkloadIdentityProvider(
        name='{0}/providers/{1}'.format(declared_pool.name, setup['terraformProvider']['id']),
        description=setup['terraformProvider']['description'],
        display_name=setup['terraformProvider']['displayName'],
        oidc= {
            'allowedAudiences': ['https://tfc.{0}'.format(org_name)],
            'issuerUri': setup['terraformProvider']['oidc']['issuerUri']
        },
        attribute_mapping=setup['terraformProvider']['attributeMapping'],
        attribute_condition='assertion.sub.startsWith("organization:{0}:project:Workspaces")'.format(terraform_org)
    )

    try:
        pool = _get_pool(declared_pool)
    except ValueError as e:
        if e.args[0] == 0:
            pool = _create_pool(declared_pool)
        else:
            raise e

    pool = _update_pool(declared_pool, pool)

    try:
        provider = _get_provider(declared_provider)
    except ValueError as e:
        if e.args[0] == 0:
            provider = _create_provider(declared_pool)
        else:
            raise e

    _update_provider(declared_provider, provider)

    return pool