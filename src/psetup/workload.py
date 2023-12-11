from googleapiclient.discovery import build
from psetup import operation

# base client for all actions on workload identity pools and providers
client = build('iam', 'v1').projects().locations().workloadIdentityPools()

class WorkloadIdentityPool:
    """A class to represent a workload identity pool in Google Cloud.

    Attributes:
        id: string, the ID for the pool, which becomes the final component
            of the resource name.
        project: string, the name of the project to create this pool in.
        display_name: string, a user-friendly name for the pool.
        description: string, a description of the pool.
        disabled: boolean, wether the pool is activated or not. Deactivated
            pools can not be used to deliver authorization tokens.
    """

    def __init__(self,
        id=None,
        project=None,
        display_name=None,
        description=None
    ):
        """Initializes the instance based on attributes.

        Args:
            id: string, the ID for the provider, which becomes the final
                component of the resource name.
            project: string, the name of the project to create this pool in.
            display_name: string, a user-friendly name for the pool.
            description: string, a description of the pool.
        """
        self.id = id
        self.project = project
        self.display_name = display_name
        self.description = description
        # the pool must always be activated in our case
        self.disabled = False

    def update_from_dict(self, body):
        """Update the instance from a dictionnary.

        Args:
            body: dict, the key-value representation of all or any part of the
                instance attributes.
        """
        try:
            self.id = body['name'].split('/workloadIdentityPools/')[-1]
        except KeyError:
            pass
        try:
            self.project = body['name'].split('/locations/')[0]
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
    def name(self):
        """Returns the fully qualified name of the instance.
        """
        fmt = '{0}/workloadIdentityPools/{1}'.format(self.parent, self.id)
        return fmt

    @property
    def parent(self):
        """Returns the fully qualified name of the parent of the instance.
        """
        fmt = '{0}/locations/global'.format(self.project)
        return fmt

class WorkloadIdentityProvider:
    """A class to represent a workload identity pool provider in Google Cloud.

    Attributes:
        id: string, the ID for the provider, which becomes the final component
            of the resource name.
        parent: string, the name of the pool to create this provider in.
        attribute_condition: string, the condition for the tokens to match.
        attribute_mapping: dict, a map of attributes between tokens.
        description: string, a description of the provider.
        display_name: string, a user-friendly name for the provider.
        oidc: dict, parameters for the openID connect protocol.
        disabled: boolean, wether the provider is activated or not. Deactivated
            providers can not be used to deliver identification tokens.
    """

    def __init__(
        self,
        id=None,
        parent=None,
        attribute_condition=None,
        attribute_mapping=None,
        description=None,
        display_name=None,
        oidc=None
    ):
        """Initializes the instance based on attributes.

        Args:
            id: string, the ID for the provider, which becomes the final
                component of the resource name.
            parent: string, the name of the pool to create this provider in.
            attribute_condition: string, the condition for the tokens to match.
            attribute_mapping: dict, a map of attributes between tokens.
            description: string, a description of the provider.
            display_name: string, a user-friendly name for the provider.
            oidc: dict, parameters for the openID connect protocol.
        """
        self.id = id
        self.parent = parent
        self.attribute_condition = attribute_condition
        self.attribute_mapping = attribute_mapping
        self.description = description
        self.disabled = False
        self.display_name = display_name
        self.oidc = oidc

    def update_from_dict(self, body):
        """Update the instance from a dictionnary.

        Args:
            body: dict, the key-value representation of all or any part of the
                instance attributes.
        """
        try:
            self.id = body['name'].split('/providers/')[-1]
        except KeyError:
            pass
        try:
            self.parent = body['name'].split('/providers/')[0]
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
    def name(self):
        """Returns the fully qualified name of the instance.
        """
        fmt = '{0}/providers/{1}'.format(self.parent, self.id)
        return fmt


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

    with client as api:
        request = api.create(
            parent=pool.parent,
            body=body,
            workloadIdentityPoolId=pool.id
        )

        initial = request.execute()
        result = operation.watch(api=api, operation=initial)

    existing_pool.update_from_dict(result)

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
    mask = _diff(declared=declared_pool, existing=existing_pool)
    # build the create request body
    body = {
        'description': declared_pool.description,
        'disabled': declared_pool.disabled,
        'displayName': declared_pool.display_name
    }

    # If there is non differences, return the original existing key.
    if mask == []:
        return existing_pool
    
    with client as api:
        request = api.patch(
            name=declared_pool.name,
            body=body,
            updateMask=','.join(mask)
        )

        initial = request.execute()
        result = operation.watch(api=api, operation=initial)

    existing_pool.update_from_dict(result)

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
        id=pool.id,
        project=pool.project
    )

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
    
    existing_pool.update_from_dict(existing)

    return existing_pool

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
        id=provider.id,
        parent=parent
    )

    with client.providers() as api:
        request = api.list(parent=parent)

        while request is not None:
            results = request.execute()
            
            for result in results['workloadIdentityPoolProviders']:
                if result['name'] == provider.name:
                    existing = result

            request = api.list_next(request, results)
    
    if existing is None:
        raise ValueError(0)
    
    existing_provider.update_from_dict(existing)

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
    mask = _diff(declared_provider, existing_provider)
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
        return existing_provider
    
    with client.providers() as api:
        request = api.patch(
            name=declared_provider.name,
            body=body,
            updateMask=','.join(mask)
        )

        initial = request.execute()
        result = operation.watch(api=api, operation=initial)

    existing_provider.update_from_dict(result)

    print('provider updated... ', end='')

    return existing_provider

def _diff(declared, existing):
    """
    Show the differences between a declared and an existing workload identity
        pool or provider.

    Args:
        declared: [WorkloadIdentityPool, WorkloadIdentityProvider], the
            delcared workload identity pool or provider.
        existing: [WorkloadIdentityPool, WorkloadIdentityProvider], the
            existing workload identity pool or provider.

    Returns:
        list, the list of attributes to update to match existing and declared.
    """
    mask = []

    for attr in existing.__dict__.keys():
        if existing.__getattribute__(attr) != declared.__getattribute__(attr):
            mask.append(attr)
    
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

    with client as api:
        request = api.create(
            parent=provider.parent,
            body=body,
            workloadIdentityPoolProviderId=provider.id
        )

        initial = request.execute()
        result = operation.watch(api=api, operation=initial)

    existing_provider.update_from_dict(result)

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
    org_name = setup['google']['org_name']
    terraform_org = setup['terraform']['organization']
    pool_id = setup['organizationPool']['id']
    condition = 'organization:{0}:project:Workspaces'.format(terraform_org)
    attribute_condition = 'assertion.sub.startsWith("{0}")'.format(condition)
    oidc = {
        'allowedAudiences': ['https://tfc.{0}'.format(org_name)],
        'issuerUri': setup['terraformProvider']['oidc']['issuerUri']
    }

    declared_pool = WorkloadIdentityPool(
        id=pool_id,
        project=project,
        description=setup['organizationPool']['description'],
        display_name=pool_id.replace('-', ' ').title()
    )
    declared_provider = WorkloadIdentityProvider(
        id=setup['terraformProvider']['id'],
        parent=declared_pool.name,
        description=setup['terraformProvider']['description'],
        display_name=setup['terraformProvider']['displayName'],
        oidc= oidc,
        attribute_mapping=setup['terraformProvider']['attributeMapping'],
        attribute_condition=attribute_condition
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