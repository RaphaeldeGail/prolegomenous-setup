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

    def diff(self, update):
        """Show the differences between the role and a declared one.

        Args:
            update: psetup.role.Role, the declared resource.

        Returns:
            list, the list of attributes to update to match existing and
                declared.
        """
        mask = []

        for attr in update.__dict__.keys():
            if isinstance(getattr(update, attr), list):
                if set(getattr(update, attr)) != set(getattr(self, attr)):
                    mask.append(attr)
            elif getattr(update, attr) != getattr(self, attr):
                mask.append(attr)

        return mask

    @property
    def name(self):
        """Returns the fully qualified name of the instance.

        Returns:
            string, the fully qualified name of the instance.
        """
        fmt = f'{self.parent}/roles/{self.role_id}'
        return fmt

def _create(role):
    """Create a role according to a resource declaration.

    Args:
        role: psetup.role.Role, the declared resource.

    Returns:
        psetup.role.Role, the role created from the operation.
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

    print('... role created... ')

    return existing_role

def _update(declared_role, existing_role):
    """Update a role according to a resource declaration.

    Args:
        declared_role: psetup.role.Role, the declared resource.
        existing_role: psetup.role.Role, the existing resource.

    Returns:
        psetup.role.Role, the role updated by the operation.
    """
    mask = existing_role.diff(declared_role)

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

    print('... role updated... ')

    return existing_role

def _get(role):
    """Get a role in a Google organization.

    Args:
        role: psetup.role.Role, the declared resource.

    Returns:
        psetup.role.Role, the existing role.

    Raises:
        IndexError, if there is no role matching the definition.
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

def apply(
    name,
    parent,
    stage,
    description=None,
    title=None,
    includedPermissions=None
    ):
    """Generate a role.

    Can either create, update or leave it as it is.

    Args:
        name: string, the ID for the role, which becomes the final component of
            the resource name.
        parent: string, the name of the organization hosting the role.
        stage: string, a stage of release for the role.
        description: string, a description of the role.
        title: string, a user-friendly name for the role.
        includedPermissions: list, a list of IAM permissions bound to the role.

    Returns:
        psetup.role.Role, the role generated according to the declaration.
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
        role= _get(declared_role)
    except IndexError as e:
        if e.args[0] == 0:
            role = _create(declared_role)

    role = _update(declared_role, role)

    return role
