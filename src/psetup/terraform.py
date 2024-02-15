"""Generate a terraform project idempotently.

Can apply a specific configuration for a project and create or update it in
order to match the configuration.

Typical usage example:

  my_project = terraform.apply(
    org_id='myOrg',
    name='myName'
  )
"""

from os import getenv
from terrasnek.api import TFC

class Project:
    """A class to represent a project in a Terraform Cloud organization.

    Attributes:
        id: string, the ID for the project, which becomes the final
            component of the resource name.
        attributes: dict, a map for the definition of the project.
        relationships: dict, a map of bounds for the project.
    """

    def __init__(self,
        project_id=None,
        name=None,
        org_id=None
    ):
        """Initializes the instance based on attributes.

        Args:
            org_id: string, the Terraform Cloud organization's ID. 
            project_id: string, the ID for the project, which becomes the final
                component of the resource name.
            name: string, the name of the project.
        """
        self.id = project_id
        self.attributes = {
            'name': name,
        }
        self.relationships = {
            'organization': {
                'data': {
                    'id': org_id,
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

def _create(declared_project):
    """Create a project according to a resource declaration.

    Args:
        declared_project: Project, the declared resource.

    Returns:
        Project, the project created from the operation.
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
        org_id=declared_project.relationships['organization']['data']['id']
    )

    try:
        TFC_TOKEN = getenv('TFC_TOKEN')
    except KeyError as e:
        raise KeyError('Empty TerraformCloud token') from e

    TFC_URL = getenv('TFC_URL', 'https://app.terraform.io')

    api = TFC(TFC_TOKEN, url=TFC_URL)
    api.set_org(declared_project.relationships['organization']['data']['id'])

    result = api.projects.create(body)

    print('... Terraform Cloud project created... ', end='')

    existing_project.update_from_dict(result['data'])

    return existing_project

def _get(declared_project):
    """Get a project in a Terraform Cloud organization.

    Args:
        declared_project: Project, the declared resource.

    Returns:
        Project, the existing project.

    Raises:
        IndexError, if there is no project matching the definition.
    """
    projects = None

    existing_project = Project(
        name=declared_project.attributes['name'],
        org_id=declared_project.relationships['organization']['data']['id']
    )

    try:
        TFC_TOKEN = getenv('TFC_TOKEN')
    except KeyError as e:
        raise KeyError('Empty TerraformCloud token') from e

    TFC_URL = getenv('TFC_URL', 'https://app.terraform.io')

    api = TFC(TFC_TOKEN, url=TFC_URL)
    api.set_org(declared_project.relationships['organization']['data']['id'])

    projects = api.projects.list_all(query=declared_project.attributes['name'])

    if not projects.get('data', []):
        raise IndexError(0)

    existing_project.update_from_dict(projects['data'][0])

    return existing_project

def apply(org_id, name):
    """Generate a project.

    Can either create, update or leave it as it is.

    Args:
        org_id: string, the Terraform Cloud organization's ID.
        name: string, the name of the project.

    Returns:
        Project, the project generated according to the declaration.
    """
    declared_project = Project(name=name, org_id=org_id)

    try:
        project = _get(declared_project)
    except IndexError as e:
        if e.args[0] == 0:
            project = _create(declared_project)

    return project
