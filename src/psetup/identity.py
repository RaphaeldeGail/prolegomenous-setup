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
            name: the name of the group in the form 'groups/{group}'.
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

class Membership:
    """A class to represent a membership in a group.

    Attributes:
        parent: string, the ID of the group hosting the member.
        account_id: string, the ID for the member, which is its email address.
        name: string, the name of the membership in the form
            'groups/{group}/memberships/{membership}'.
        roles: list, a list of roles for the member, to choose between 'OWNER',
            'MANAGER' and 'MEMBER'.
    """

    def __init__(self,
        parent=None,
        account_id=None,
        name=None,
        roles=None
    ):
        """Initializes the instance based on attributes.

        Args:
        parent: string, the ID of the group hosting the member.
        account_id: string, the ID for the member, which is its email address.
        name: string, the name of the membership in the form
            'groups/{group}/memberships/{membership}'.
        roles: list, a list of roles for the member, to choose between 'OWNER',
            'MANAGER' and 'MEMBER'.
        """
        self.parent = parent
        self.account_id = account_id
        self.name = name
        self.roles = roles

    def update_from_dict(self, body):
        """Update the instance from a dictionnary.

        Args:
            body: dict, the key-value representation of all or any part of the
                instance attributes.
        """
        try:
            self.account_id = body['preferredMemberKey']['id']
        except KeyError:
            pass
        try:
            self.name = body['name']
        except KeyError:
            pass
        try:
            self.roles = [ role['name'] for role in body['roles'] ]
        except KeyError:
            pass
        try:
            self.parent = body['name'].split('/')[0]
        except KeyError:
            pass

def _create_group(group):
    """
    Create a Google group according to a resource declaration.

    Args:
        group: Group, the declared resource.

    Returns:
        Group, the group created from the operation.
    """
    # build the create request body
    body = {
        "description": group.description,
        "displayName": group.display_name,
        "groupKey": {
        "id": group.group_id
        },
        "labels": {
        "cloudidentity.googleapis.com/groups.discussion_forum": "",
        },
        "parent": group.parent
    }

    existing_group = Group(
        group_id=group.group_id,
        parent=group.parent
    )
    # long running operation
    with build('cloudidentity', 'v1').groups() as api:
        request = api.create(
            body=body,
            initialGroupConfig='WITH_INITIAL_OWNER'
        )

        result = request.execute()

    existing_group.update_from_dict(result)

    print('... Google group created... ')

    return existing_group

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

def _create_membership(membership):
    """
    Create a Google group membership according to a resource declaration.

    Args:
        membership: Membership, the declared membership.

    Returns:
        Membership, the membership created from the operation.
    """
    # build the create request body
    body = {
        "preferredMemberKey": {
            "id": membership.account_id,
        },
        "roles": [
            { 
                "name": role,
            } for role in membership.roles
        ]
    }

    existing_membership = Membership(
        account_id=membership.account_id,
        parent=membership.parent
    )
    # long running operation
    with build('cloudidentity', 'v1').groups().memberships() as api:
        request = api.create(
            parent=membership.parent,
            body=body
        )

        result = request.execute()

    existing_membership.update_from_dict(result)

    print('... membership created... ')

    return existing_membership

def _get_membership(membership):
    """Get a membership in a Google group.

    Args:
        membership: Membership, the delcared resource.

    Returns:
        Membership, the existing membership.

    Raises:
        IndexError, if there is no membership matching the definition.
    """ 
    existing = None

    existing_membership = Membership(
        account_id=membership.account_id,
        parent=membership.parent
    )

    with build('cloudidentity', 'v1').groups().memberships() as api:
        request = api.list(parent=existing_membership.parent)

        while request is not None:
            results = request.execute()

            for result in results.get('memberships', []):
                if result['preferredMemberKey']['id'] == existing_membership.account_id:
                    existing = result

            request = api.list_next(request, results)

    if existing is None:
        raise IndexError(0)

    existing_membership.update_from_dict(existing)

    return existing_membership

def apply_membership(parent, email, roles):
    """Generate a membership in a Google group.
    
    Can either create, update or leave it as it is.

    Args:
        parent: string, the ID of the group hosting the member.
        email: string, the email address of the member.
        roles: list, a list of roles for the member, to choose between 'OWNER',
            'MANAGER' and 'MEMBER'.

    Returns:
        Membership, the membership generated according to the declaration.
    """
    declared_membership= Membership(
        account_id=email,
        parent=parent,
        roles=roles
    )

    try:
        membership = _get_membership(declared_membership)
    except IndexError as e:
        if e.args[0] == 0:
            membership = _create_membership(declared_membership)

    return membership