"""Generate an organization role idempotently.

Can apply a specific configuration for a role and create or update it in
order to match the configuration.

Typical usage example:

  my_role = role.apply(
    name='myRoleName',
    parent='parent',
    stage='GA',
    description='',
    title='displayName',
    includedPermissions=[permissions])
"""

from googleapiclient.discovery import build

class Role:
    """A class to represent a role in a Google Cloud organization.

    Attributes:
        role_id: string, the ID for the role, which becomes the final component
            of the resource name.
        parent: string, the name of the organization hosting the role.
        description: string, a description of the role.
        title: string, a user-friendly name for the role.
        stage: string, a stage of release for the role.
        includedPermissions: list, a list of IAM permissions bound to the role.
    """

    def __init__(self,
        parent=None,
        includedPermissions=None,
        stage=None,
        title=None,
        role_id=None,
        description=None
    ):
        """Initializes the instance based on attributes.

        Args:
            parent: string, the name of the organization hosting the role.
            includedPermissions: list, a list of IAM permissions bound to the
                role.
            stage: string, a stage of release for the role.
            title: string, a user-friendly name for the role.
            role_id: string, the ID for the role, which becomes the final component
            of the resource name.
            description: string, a description of the role.
        """
        self.role_id = role_id
        self.parent = parent
        self.description = description
        self.title = title
        self.stage = stage
        self.includedPermissions = includedPermissions

    def update_from_dict(self, body):
        """Update the instance from a dictionnary.

        Args:
            body: dict, the key-value representation of all or any part of the
                instance attributes.
        """
        try:
            self.role_id = body['name'].split('/roles/')[-1]
        except KeyError:
            pass
        try:
            self.parent = body['name'].split('/roles/')[0]
        except KeyError:
            pass
        try:
            self.description = body['description']
        except KeyError:
            pass
        try:
            self.title = body['title']
        except KeyError:
            pass
        try:
            self.stage = body['stage']
        except KeyError:
            pass
        try:
            self.includedPermissions = body['includedPermissions']
        except KeyError:
            pass

    @property
    def name(self):
        """Returns the fully qualified name of the instance.

        Returns:
            string, the fully qualified name of the instance.
        """
        fmt = f'{self.parent}/roles/{self.role_id}'
        return fmt

def _create_role(role):
    """
    Create a role according to a declared one.

    Args:
        role: Role, the delcared service account.

    Returns:
        Role, the role as a result from the operation.
    """
    # build the create request body
    body = {
        'roleId': role.role_id,
        'role': {
            'description': role.description,
            "includedPermissions": role.includedPermissions,
            'stage': role.stage,
            "title": role.title
        }
    }

    existing_role = Role(
        role_id=role.role_id,
        parent=role.parent
    )

    with build('iam', 'v1').organizations().roles() as api:
        request = api.create(
            parent=role.parent,
            body=body,
        )

        result = request.execute()

    existing_role.update_from_dict(result)

    print('role created... ', end='')

    return existing_role

def _update_role(declared_role, existing_role):
    """
    Update an existing service account compared to a declared one.

    Args:
        declared_sa: ServiceAccount, the declared service account.
        existing_sa: ServiceAccount, the existing service account.

    Returns:
        ServiceAccount, the service account updated from the operation.
    """
    mask = _diff(declared=declared_role, existing=existing_role)

    # If there is non differences, return the original existing account.
    if not mask:
        return existing_role

    # build the update request body
    body = {
        'description': declared_role.description,
        'includedPermissions': declared_role.includedPermissions,
        'name': declared_role.name,
        'stage': declared_role.stage,
        'title': declared_role.title
    }

    existing_role = Role(
        role_id=declared_role.role_id,
        parent=declared_role.parent
    )

    with build('iam', 'v1').organizations().roles() as api:
        request = api.patch(
            name=declared_role.name,
            body=body,
            updateMask=','.join(mask)
        )

        result = request.execute()

    existing_role.update_from_dict(result)

    print('role updated... ', end='')

    return existing_role

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
        if isinstance(getattr(existing, attr), list):
            if set(getattr(existing, attr)) != set(getattr(declared, attr)):
                mask.append(attr)
        elif getattr(existing, attr) != getattr(declared, attr):
            mask.append(attr)

    return mask

def _get_role(role):
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
    existing = None

    existing_role = Role(
        role_id=role.role_id,
        parent=role.parent
    )

    with build('iam', 'v1').organizations().roles() as api:
        request = api.list(parent=role.parent)

        while request is not None:
            results = request.execute()

            if 'roles' in results:
                for result in results['roles']:
                    if result['name'] == role.name:
                        existing = result

            request = api.list_next(request, results)

    if existing is None:
        raise IndexError(0)

    # Only the get method can render the includedPermissions in its response
    with build('iam', 'v1').organizations().roles() as api:
        request = api.get(name=existing['name'])
        existing = request.execute()

    existing_role.update_from_dict(existing)

    return existing_role

def apply_role(
    name,
    parent,
    stage,
    description=None,
    title=None,
    includedPermissions=None
    ):
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
    declared_role = Role(
        role_id=name,
        description=description,
        parent=parent,
        stage=stage,
        title=title,
        includedPermissions=includedPermissions
    )

    try:
        role= _get_role(declared_role)
    except IndexError as e:
        if e.args[0] == 0:
            role = _create_role(declared_role)

    role = _update_role(declared_role, role)

    return role
