"""Generate a builder service account idempotently.

Can apply a specific configuration for a service account and create or update
it in order to match the configuration.

Typical usage example:

  service_account = generate_service_account(setup, parent, poolId)
"""

from googleapiclient.discovery import build

# base client for all actions on workload identity pools and providers
client = build('iam', 'v1').projects().serviceAccounts()

class ServiceAccount:
    """A class to represent a service account in Google Cloud project.

    Attributes:
        account_id: string, the ID for the service account, which becomes the
            final component of the resource name.
        description: string, a description of the service account.
        display_name: string, a user-friendly name for the service account.
        project: string, the ID of the project to create this account in.

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
            project: string, the ID of the project to create this account in.
            display_name: string, a user-friendly name for the service account.
            description: string, a description of the service account.
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

    @property
    def name(self):
        """Returns the fully qualified name of the instance.
        """
        project_id = f'projects/{self.project}'
        sa = f'{self.account_id}@{self.project}.iam.gserviceaccount.com'
        fmt = f'{project_id}/serviceAccounts/{sa}'
        return fmt

def _create_sa(sa):
    """
    Create a service account according to a declared one.

    Args:
        sa: ServiceAccount, the delcared service account.

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

    with client as api:
        request = api.create(
            name=f'projects/{sa.project}',
            body=body,
        )

        result = request.execute()

    existing_sa.update_from_dict(result)

    print('service account created... ', end='')

    return existing_sa

def _update_sa(declared_sa, existing_sa):
    """
    Update an existing service account compared to a declared one.

    Args:
        declared_sa: ServiceAccount, the declared service account.
        existing_sa: ServiceAccount, the existing service account.

    Returns:
        ServiceAccount, the service account updated from the operation.
    """
    mask = _diff(declared=declared_sa, existing=existing_sa)
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

    with client as api:
        request = api.patch(
            name=declared_sa.name,
            body=body
        )

        result = request.execute()

    existing_sa.update_from_dict(result)

    print('service account updated... ', end='')

    return existing_sa

def _diff(declared, existing):
    """
    Show the differences between a declared and an existing service account.

    Args:
        declared: ServiceAccount, the declared service account.
        existing: ServiceAccount, the existing service account.

    Returns:
        list, the list of attributes to update to match existing and declared.
    """
    mask = []

    for attr in existing.__dict__.keys():
        if getattr(existing, attr) != getattr(declared, attr):
            mask.append(attr)

    return mask

def _get_sa(sa):
    """
    Get the existing service account in project corresponding to the
        declared service account.

    Args:
        sa: ServiceAccount, the delcared service account.

    Returns:
        ServiceAccount, the existing service account.

    Raises:
        ValueError, if there is no service account matching the
            definition.
    """
    parent = f'projects/{sa.project}'
    existing = None

    existing_sa = ServiceAccount(
        account_id=sa.account_id,
        project=sa.project
    )

    with client as api:
        request = api.list(name=parent)

        while request is not None:
            results = request.execute()

            for result in results['accounts']:
                if result['name'] == sa.name:
                    existing = result

            request = api.list_next(request, results)

    if existing is None:
        raise ValueError(0)

    existing_sa.update_from_dict(existing)

    return existing_sa

def _control_access(sa, policy):
    """
    Apply IAM policy to the tag key.

    Args:
        sa: ServiceAccount, the delcared service account.
        policy: dict, list all `bindings` to apply to the account policy.
    """
    with client as api:
        request = api.setIamPolicy(resource=sa.name, body=policy)
        request.execute()

    print('IAM policy set... ', end='')

    return None

def generate_service_account(setup, parent, pool_id):
    """Generate the builder servie account for the root structure.
    
    Can either create, update or leave it as it is.

    Args:
        setup: dict, the configuration used to build the root structure.
        parent: string, the ID of the project hosting the service account.
        pool_id: string, the name of the workload identity pool that can
            delegate access to the service account.

    Returns:
        ServiceAccount, the generated service account.
    """
    account_id = setup['builderAccount']['name']
    exec_gr = f'group:{setup["google"]["groups"]["executive_group"]}'
    wrk_id = setup['terraform']['workspace_project']
    pool = f'principalSet://iam.googleapis.com/{pool_id}'
    principal = f'{pool}/attribute.terraform_project_id/{wrk_id}'
    policy = {
        'policy': {
            'bindings': [
                {
                    'members': [ exec_gr ],
                    'role': 'roles/iam.serviceAccountTokenCreator',
                },
                {
                    'members': [ principal ],
                    'role': 'roles/iam.workloadIdentityUser',
                },
            ],
        },
    }

    declared_sa = ServiceAccount(
        account_id=account_id,
        project=parent,
        display_name=setup['builderAccount']['displayName'],
        description=setup['builderAccount']['description']
    )

    try:
        sa = _get_sa(declared_sa)
    except ValueError as e:
        if e.args[0] == 0:
            sa = _create_sa(declared_sa)
        else:
            raise e

    sa = _update_sa(declared_sa, sa)

    _control_access(sa, policy)

    return sa
