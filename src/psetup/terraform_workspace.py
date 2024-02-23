"""Generate a terraform workspace idempotently.

Can apply a specific configuration for a workspace and create or update it in
order to match the configuration.

Typical usage example:

  my_workspace = terraform.apply(
    org_id='myOrganization',
    name='myName',
    description='',
    repo_id='my/repo'
  )
"""

from os import getenv
from terrasnek.api import TFC
from psetup.terraform_variable import Variable

class Workspace:
    """A class to represent a workspace in a Terraform Cloud organization.

    Attributes:
        id: string, the ID for the workspace, which becomes the final
            component of the resource name.
        attributes: dict, a map for the definition of the variable set.
        project: string, the id of the project hosting the workspace.
    """
    def __init__(self, wrk_id=None, name=None, description=None, repo_id=None, oauth_token=None, project=None):
        """Initializes the instance based on attributes.

        Args:
            wrk_id: string, the ID for the workspace, which becomes the final
                component of the resource name.
            name: string, the name of the workspace.
            project: string, the ID of the project hosting the workspace.
            description: string, a description of the workspace.
            repo_id: string, the repository name used as a version controlling source.
            oauth_token: string, the oauth token ID for authenticating against the version controlling source.
        """
        self.id = wrk_id
        self.attributes = {
            "allow-destroy-plan": True,
            "auto-apply": True,
            "auto-apply-run-trigger": True,
            "auto-destroy-activity-duration": "14d",
            "environment": "default",
            "name": name,
            "queue-all-runs": False,
            "speculative-enabled": True,
            "structured-run-output-enabled": True,
            "terraform-version": "1.2.0",
            "working-directory": "/terraform",
            "global-remote-state": False,
            "execution-mode": "remote",
            "vcs-repo": {
                "identifier": repo_id,
                "oauth-token-id": oauth_token
            },
            "description": description,
            "file-triggers-enabled": True,
            "trigger-patterns": [
                "/terraform/*.tf"
            ],
            "source-name": "modest python client",
            "setting-overwrites": {
                "execution-mode": False,
                "agent-pool": False
            }
        }
        self.project = project

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
            self.project = body['relationships']['project']['data']['id']
        except KeyError:
            pass

def _build(org_id):
    """Build an API client for a Terraform Cloud organization.

    Args:
        org_id: string, the Terraform Cloud organization's ID.

    Returns:
        terrasnek.api.TFC , the api client for the organization.
    """
    try:
        TFC_TOKEN = getenv('TFC_TOKEN')
    except KeyError as e:
        raise KeyError('Empty TerraformCloud token') from e

    TFC_URL = getenv('TFC_URL', 'https://app.terraform.io')

    api = TFC(TFC_TOKEN, url=TFC_URL)
    api.set_org(org_id)

    return api

def _create_variable(org_id, wrk_id, declared_variable):
    """Create a variable according to a resource declaration.

    Args:
        org_id: string, the Terraform Cloud organization's ID.
        wrk_id: string, the workspace ID hosting the variable.
        declared_variable: Variable, the declared resource.

    Returns:
        Variable, the variable created from the operation.
    """
    body = {
        'data': {
            'attributes': declared_variable.attributes,
            'type': 'vars'
        }
    }

    existing_variable = Variable(
        key=declared_variable.attributes['key']
    )

    result = _build(org_id).workspace_vars.create(wrk_id, body)

    print('... Terraform Cloud variable created... ')

    existing_variable.update_from_dict(result['data'])

    return existing_variable

def _update_variable(org_id, wrk_id, declared_variable, existing_variable):
    """Update a variable according to a resource declaration.

    Args:
        org_id: string, the Terraform Cloud organization's ID.
        wrk_id: string, the workspace ID hosting the variable.    
        declared_variable: Variable, the declared resource.
        existing_variable: Variable, the existing resource.

    Returns:
        Variable, the variable updated by the operation.
    """
    mask = existing_variable.diff(declared_variable)

    # If there is non differences, return the original existing variable.
    if not mask:
        return existing_variable

    body = {
        'data': {
            'attributes': declared_variable.attributes,
            'type': 'vars'
        }
    }

    result = _build(org_id).workspace_vars.update(
        wrk_id,
        existing_variable.id,
        body
    )

    existing_variable.update_from_dict(result['data'])

    print('... variable updated... ')

    return existing_variable

def _get_variable(org_id, wrk_id, declared_variable):
    """Get a variable in a Terraform Cloud organization.

    Args:
        org_id: string, the Terraform Cloud organization's ID.
        wrk_id: string, the workspace ID hosting the variable.
        declared_variable: Variable, the declared resource.

    Returns:
        Variable, the existing variable.

    Raises:
        IndexError, if there is no variable matching the definition.
    """
    exists = False

    existing_variable = Variable(
        key=declared_variable.attributes['key']
    )

    variables = _build(org_id).workspace_vars.list(wrk_id)

    for variable in variables.get('data', []):
        if variable['attributes']['key'] == declared_variable.attributes['key']:
            exists = True
            existing_variable.update_from_dict(variable)

    if not exists:
        raise IndexError(0)

    return existing_variable

def apply_variable(
        org_id,
        wrk_id,
        key,
        value,
        category,
        sensitive=False,
        hcl=False,
        description=None
    ):
    """Generate a variable.

    Can either create, update or leave it as it is.

    Args:
        org_id: string, the Terraform Cloud organization's ID.
        wrk_id: string, the workspace ID hosting the variable.
        key: string, the name of the variable.
        value: string, the value of the variable.
        sensitive: bool, whether the value is sensitive. If true, variable is
            not visible in the UI.
        category: string, whether this is a Terraform or environment variable.
            Valid values are "terraform" or "env".
        hcl: bool, whether to evaluate the value of the variable as a string of
            HCL code. Has no effect for environment variables.
        description: string, a description of the variable.

    Returns:
        Variable, the variable generated according to the declaration.
    """
    declared_variable = Variable(
        key=key,
        value=value,
        sensitive=sensitive,
        category=category,
        hcl=hcl,
        description=description
    )

    try:
        variable = _get_variable(org_id, wrk_id, declared_variable)
    except IndexError as e:
        if e.args[0] == 0:
            variable = _create_variable(org_id, wrk_id, declared_variable)

            return variable

    variable = _update_variable(org_id, wrk_id, declared_variable, variable)

    return variable

def _create(org_id, declared_workspace):
    """Create a workspace according to a resource declaration.

    Args:
        org_id: string, the Terraform Cloud organization's ID.
        declared_workspace: Workspace, the declared resource.

    Returns:
        Workspace, the workspace created from the operation.
    """
    body = {
        'data': {
            'type': 'workspaces',
            'attributes': declared_workspace.attributes,
            'relationships': {
                'project': {
                    'data': {
                            'id': declared_workspace.project,
                            'type': 'projects'
                    }
                }
            }
        }
    }

    existing_workspace = Workspace(
        name=declared_workspace.attributes['name']
    )

    result = _build(org_id).workspaces.create(body)

    print('... Terraform Cloud workspace created... ')

    existing_workspace.update_from_dict(result['data'])

    return existing_workspace

def _get(org_id, declared_workspace):
    """Get a workspace in a Terraform Cloud organization.

    Args:
        org_id: string, the Terraform Cloud organization's ID.
        declared_workspace: Workspace, the declared resource.

    Returns:
        Workspace, the existing workspace.

    Raises:
        IndexError, if there is no workspace matching the definition.
    """
    exists = False

    existing_workspace = Workspace(
        name=declared_workspace.attributes['name']
    )

    workspaces = _build(org_id).workspaces.list_all(search=f'{declared_workspace.attributes["name"]}')

    for workspace in workspaces.get('data', []):
        if workspace['attributes']['name'] == \
                                        declared_workspace.attributes['name']:
            exists = True
            existing_workspace.update_from_dict(workspace)

    if not exists:
        raise IndexError(0)

    return existing_workspace

def apply(name, org_id, project, repo_id, description, oauth_token):
    """Generate a workspace.

    Can either create, update or leave it as it is.

    Args:
        org_id: string, the Terraform Cloud organization's ID.
        name: string, the name of the project.

    Returns:
        Workspace, the workspace generated according to the declaration.
    """
    declared_workspace = Workspace(
        name=name,
        description=description,
        repo_id=repo_id,
        oauth_token=oauth_token,
        project=project
    )

    try:
        wrk = _get(org_id, declared_workspace)
    except IndexError as e:
        if e.args[0] == 0:
            wrk= _create(org_id, declared_workspace)

    return wrk
