"""Generate a Google group idempotently.

Can apply a specific configuration for a group and create or update it in order
to match the configuration.

Typical usage example:

    my_group = identity.apply_group(
        project='project',
        id=''myServiceAccountName',
        displayName='myDisplayName',
        description='')

    identity.apply_member(my_group, {Member})
"""

from googleapiclient.discovery import build

class Group:
    """A class to represent a Google group.

    Attributes:
        group_id: string, the ID for the group, which is its
            email address.
        display_name: string, a user-friendly name for the group.
        description: string, a description of the group.
        parent: string, the ID of the customers directory hosting the
            group.
        name: the name of the group in the form 'groups/{group}'
    """

    def __init__(self,
        group_id=None,
        parent=None,
        name=None,
        display_name=None,
        description=None
    ):
        """Initializes the instance based on attributes.

        Args:
            group_id: string, the ID for the group, which is its
                email address.
            display_name: string, a user-friendly name for the group.
            description: string, a description of the group.
            parent: string, the ID of the customers directory hosting the
                group.
            name: the name of the group in the form 'groups/{group}'
        """
        self.name = name
        self.group_id = group_id
        self.parent = parent
        self.description = description
        self.display_name = display_name

    def update_from_dict(self, body):
        """Update the instance from a dictionnary.

        Args:
            body: dict, the key-value representation of all or any part of the
                instance attributes.
        """
        try:
            self.group_id = body['groupKey']['id']
        except KeyError:
            pass
        try:
            self.parent = body['parent']
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
            self.name = body['name']
        except KeyError:
            pass

def _create_group(declared_group):
    return None

def _get_group(group):
    """Get a group in a Google Customers Directory.

    Args:
        group: Group, the delcared resource.

    Returns:
        Group, the existing group.

    Raises:
        IndexError, if there is no group matching the definition.
    """
    existing = None

    existing_group = Group(
        group_id=group.group_id,
        parent=group.parent
    )

    with build('cloudidentity', 'v1').groups() as api:
        request = api.list(parent=existing_group.parent)

        while request is not None:
            results = request.execute()

            for result in results.get('groups', []):
                if result['groupKey']['id'] == existing_group.group_id:
                    existing = result

            request = api.list_next(request, results)

    if existing is None:
        raise IndexError(0)

    existing_group.update_from_dict(existing)

    return existing_group

def apply_group(email, parent, displayName, description):
    """Generate a Google group.
    
    Can either create, update or leave it as it is.

    Args:
        name: string, the ID for the service account, which becomes the
            final component of the resource name.
        description: string, a description of the service account.
        displayName: string, a user-friendly name for the service account.
        project: string, the ID of the project hosting the account.

    Returns:
        Group, the Google group generated according to the
            declaration.
    """
    declared_group= Group(
        group_id=email,
        parent=parent,
        display_name=displayName,
        description=description
    )

    try:
        group = _get_group(declared_group)
    except IndexError as e:
        if e.args[0] == 0:
            group = _create_group(declared_group)

    return group

def apply_member():
    return None