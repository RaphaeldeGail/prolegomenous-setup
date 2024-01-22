from os import getenv
from terrasnek.api import TFC

class Project:
    """A class to represent a service account in Google Cloud project.

    Attributes:
        account_id: string, the ID for the service account, which becomes the
            final component of the resource name.
        description: string, a description of the service account.
        display_name: string, a user-friendly name for the service account.
        project: string, the ID of the project to create this account in.

    """

    def __init__(self,
        id=None,
        name=None,
        organization=None
    ):
        """Initializes the instance based on attributes.

        Args:
            account_id: string, the ID for the service account, which becomes
                the final component of the resource name.
            project: string, the ID of the project to create this account in.
            display_name: string, a user-friendly name for the service account.
            description: string, a description of the service account.
        """
        self.id = id
        self.attributes = {
            'name': name,
        }
        self.relationships = {
            'organization': {
                'data': {
                    'id': organization,
                    'type': 'organizations'
                },
            }
        }

    def update_from_dict(self, body):
        """Update the instance from a dictionnary.

        Args:
            body: dict, the key-value representation of all or any part of the
                instance attributes.
        """
        try:
            self.id = body['id']
        except KeyError:
            pass
        try:
            self.attributes = body['attributes']
        except KeyError:
            pass
        try:
            self.relationships = body['relationships']
        except KeyError:
            pass

def _create_project(declared_project):
    """
    Create a service account according to a declared one.

    Args:
        sa: ServiceAccount, the delcared service account.

    Returns:
        ServiceAccount, the service account created from the operation.
    """
    body = {
        'data': {
            'attributes': {
                'name': declared_project.attributes['name']
            },
            'type': 'projects'
        }
    }

    existing_project = Project(
        name=declared_project.attributes['name'],
        organization=declared_project.relationships['organization']['data']['id']
    )

    try:
        TFC_TOKEN = getenv('TFC_TOKEN')
    except KeyError as e:
        raise KeyError('Empty TerraformCloud token') from e

    TFC_URL = getenv('TFC_URL', 'https://app.terraform.io')

    api = TFC(TFC_TOKEN, url=TFC_URL)
    api.set_org(declared_project.relationships['organization']['data']['id'])

    result = api.projects.create(body)

    print('Terraform Cloud project created... ', end='')

    existing_project.update_from_dict(result['data'])

    return existing_project

def _get_project(declared_project):
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
    projects = None

    existing_project = Project(
        name=declared_project.attributes['name'],
        organization=declared_project.relationships['organization']['data']['id']
    )

    try:
        TFC_TOKEN = getenv('TFC_TOKEN')
    except KeyError as e:
        raise KeyError('Empty TerraformCloud token') from e

    TFC_URL = getenv('TFC_URL', 'https://app.terraform.io')

    api = TFC(TFC_TOKEN, url=TFC_URL)
    api.set_org(declared_project.relationships['organization']['data']['id'])

    projects = api.projects.list_all(query=declared_project.attributes['name'])

    if projects is None:
        raise IndexError(0)

    existing_project.update_from_dict(projects['data'][0])

    return existing_project

def apply_project(organization, project):
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
    declared_project = Project(name=project, organization=organization)

    try:
        project = _get_project(declared_project)
    except IndexError as e:
        if e.args[0] == 0:
            project = _create_project(declared_project)

    return project
