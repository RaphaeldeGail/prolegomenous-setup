"""Generate a service account idempotently.

Can apply a specific configuration for a service account and create or update
it in order to match the configuration.

Typical usage example:

    my_sa = service_account.apply(
        project='project',
        id=''myServiceAccountName',
        displayName='myDisplayName',
        description='')

    service_account.control(my_sa, {ServiceAccountPolicy})
"""

from googleapiclient.discovery import build

class ServiceAccount:
    """A class to represent a service account in a Google Cloud project.

    Attributes:
        account_id: string, the ID for the service account, which becomes the
            final component of the resource name.
        description: string, a description of the service account.
        display_name: string, a user-friendly name for the service account.
        project: string, the ID of the project hosting the account.

    """

    def __init__(self,
        account_id=None,
        project=None,
        display_name=None,
        description=None
    ):
        """Initializes the instance based on attributes.

        Args:
            account_id: string, the ID for the service account, which becomes
                the final component of the resource name.
            description: string, a description of the service account.
            display_name: string, a user-friendly name for the service account.
            project: string, the ID of the project hosting the account.
        """
        self.account_id = account_id
        self.project = project
        self.description = description
        self.display_name = display_name

    def update_from_dict(self, body):
        """Update the instance from a dictionnary.

        Args:
            body: dict, the key-value representation of all or any part of the
                instance attributes.
        """
        try:
            email = body['name'].split('/serviceAccounts/')[-1]
            self.account_id = email.split('@')[0]
        except KeyError:
            pass
        try:
            full_name = body['name'].split('/serviceAccounts/')[0]
            self.project = full_name.split('/')[-1]
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

    def diff(self, update):
        """Show the differences between the service account and a declared one.

        Args:
            update: psetup.service_account.ServiceAccount, the declared
                resource.

        Returns:
            list, the list of attributes to update to match existing and
                declared.
        """
        mask = []

        for attr in update.__dict__.keys():
            if getattr(update, attr) != getattr(self, attr):
                mask.append(attr)

        return mask

    @property
    def name(self):
        """Returns the fully qualified name of the instance.

        Returns:
            string, the fully qualified name of the instance.
        """
        project_id = f'projects/{self.project}'
        sa = f'{self.account_id}@{self.project}.iam.gserviceaccount.com'
        fmt = f'{project_id}/serviceAccounts/{sa}'
        return fmt

    @property
    def email(self):
        """Returns the email address of the instance.

        Returns:
            string, the email of the instance.
        """
        fmt = self.name.split('/serviceAccounts/')[1]
        return fmt

def _create(sa):
    """
    Create a service account according to a resource declaration.

    Args:
        sa: ServiceAccount, the declared resource.

    Returns:
        ServiceAccount, the service account created from the operation.
    """
    # build the create request body
    body = {
        'accountId': sa.account_id,
        'serviceAccount': {
            'description': sa.description,
            'displayName': sa.display_name
        }
    }

    existing_sa = ServiceAccount(
        account_id=sa.account_id,
        project=sa.project
    )

    with build('iam', 'v1').projects().serviceAccounts() as api:
        request = api.create(
            name=f'projects/{sa.project}',
            body=body,
        )

        result = request.execute()

    existing_sa.update_from_dict(result)

    print('... service account created... ')

    return existing_sa

def _update(declared_sa, existing_sa):
    """
    Update a service account according to a resource declaration.

    Args:
        declared_sa: ServiceAccount, the declared resource.
        existing_sa: ServiceAccount, the existing resource.

    Returns:
        ServiceAccount, the service account updated by the operation.
    """
    mask = existing_sa.diff(declared_sa)
    # build the update request body
    body = {
        'serviceAccount': {
            'description': declared_sa.description,
            'displayName': declared_sa.display_name
        },
        'updateMask': ','.join(mask)
    }

    existing_sa = ServiceAccount(
        account_id=declared_sa.account_id,
        project=declared_sa.project
    )

    # If there is non differences, return the original existing account.
    if not mask:
        return existing_sa

    with build('iam', 'v1').projects().serviceAccounts() as api:
        request = api.patch(
            name=declared_sa.name,
            body=body
        )

        result = request.execute()

    existing_sa.update_from_dict(result)

    print('... service account updated... ')

    return existing_sa

def _get(sa):
    """Get a service account in a Google Cloud project.

    Args:
        sa: ServiceAccount, the delcared resource.

    Returns:
        ServiceAccount, the existing service account.

    Raises:
        IndexError, if there is no service account matching the definition.
    """
    parent = f'projects/{sa.project}'
    existing = None

    existing_sa = ServiceAccount(
        account_id=sa.account_id,
        project=sa.project
    )

    with build('iam', 'v1').projects().serviceAccounts() as api:
        request = api.list(name=parent)

        while request is not None:
            results = request.execute()

            for result in results.get('accounts', []):
                if result['name'] == sa.name:
                    existing = result

            request = api.list_next(request, results)

    if existing is None:
        raise IndexError(0)

    existing_sa.update_from_dict(existing)

    return existing_sa

def control(service_account, policy):
    """Apply IAM policy to the service account.

    Args:
        sa: ServiceAccount, the delcared resource.
        policy: google.iam.v1.policy_pb2.Policy, the policy to apply.
    """
    # Match the body to the definition of service account setIamPolicy method.
    # members is of type RepeatedScalerContainer and must be set to a list.
    body = {
        'policy': {
            'bindings': [
                {
                    'role': binding.role,
                    'members': list(binding.members)
                } for binding in policy.bindings
            ]
        }
    }

    with build('iam', 'v1').projects().serviceAccounts() as api:
        request = api.setIamPolicy(resource=service_account.name, body=body)
        request.execute()

    return None

def apply(project, name, displayName, description):
    """Generate a service account.
    
    Can either create, update or leave it as it is.

    Args:
        name: string, the ID for the service account, which becomes the
            final component of the resource name.
        description: string, a description of the service account.
        displayName: string, a user-friendly name for the service account.
        project: string, the ID of the project hosting the account.

    Returns:
        ServiceAccount, the service account generated according to the
            declaration.
    """
    declared_service_account = ServiceAccount(
        project=project.project_id,
        account_id=name,
        display_name=displayName,
        description=description
    )

    try:
        service_account = _get(declared_service_account)
    except IndexError as e:
        if e.args[0] == 0:
            service_account = _create(declared_service_account)

    service_account = _update(declared_service_account, service_account)

    return service_account
