"""Generate a terraform variable set idempotently.

Can apply a specific configuration for a variable set or variable and create or
update it in order to match the configuration.

Typical usage example:

  my_varset = terraform_variable.apply(
    org_id='myOrg',
    name='nyName',
    description='',
    project='projectId')

  my_var = terraform_variable.apply_variable(
    org_id='myOrg',
    varset_id=my_varset.id,
    key='myKey',
    value='myValue',
    category='env',
    description=''
  )
"""

from os import getenv
from terrasnek.api import TFC

class Variable:
    """A class to represent a variable in a Terraform Cloud organization.

    Attributes:
        id: string, the ID for the variable, which becomes the final component
            of the resource name.
        attributes: dict, a map for the definition of the variable.
    """

    def __init__(self,
        id=None,
        key=None,
        value=None,
        sensitive=None,
        category=None,
        hcl=None,
        description=None
    ):
        """Initializes the instance based on attributes.

        Args:
            id: string, the ID for the variable, which becomes the final
                component of the resource name.
            key: string, the name of the variable.
            value: string, the value of the variable.
            sensitive: bool, whether the value is sensitive. If true, variable
                is not visible in the UI.
            category: string, whether this is a Terraform or environment
                variable. Valid values are "terraform" or "env".
            hcl: bool, whether to evaluate the value of the variable as a
                string of HCL code. Has no effect for environment variables.
            description: string, a description of the variable.
        """
        self.id = id
        self.attributes = {
            'key': key,
            'value': value,
            'sensitive': sensitive,
            'category': category,
            'hcl': hcl,
            'description': description
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

    def diff(self, other):
        """Show the differences between the variable and a declared one.

        Args:
            other: Variable, the declared resource.

        Returns:
            list, the list of attributes to update to match existing and
                declared.
        """
        mask = []

        for attr in other.attributes:
            if other.attributes[attr] != self.attributes.get(attr, None):
                mask.append(attr)

        return mask

class VariableSet:
    """A class to represent a variable set in a Terraform Cloud organization.

    Attributes:
        id: string, the ID for the variable set, which becomes the final
            component of the resource name.
        attributes: dict, a map for the definition of the variable set.
        projects: list, a list of project linked to the variable set.
    """

    def __init__(self,
            id=None,
            name=None,
            description=None,
            project=None,
            glob=False
        ):
        """Initializes the instance based on attributes.

        Args:
            id: string, the ID for the variable set, which becomes the final
                component of the resource name.
            name: string, the name of the variable set.
            project: string, the ID of the project to link to the variable set.
            glob: bool, whether the variable set should be applied globally, or
                only specifically on certain projects.
            description: string, a description of the variable set.
        """
        self.id = id
        self.attributes = {
            "name": name,
            "description": description,
            "global": glob,
            "priority": False
        }
        if project is not None:
            self.projects = [
                {
                    "id": project,
                    "type": "projects"
                }
            ]
        else:
            self.projects = []
        
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
            self.projects = body['relationships']['projects']['data']
        except KeyError:
            pass

    def diff(self, other):
        """Show the differences between the variable set and a declared one.

        Args:
            other: VariableSet, the declared resource.

        Returns:
            list, the list of attributes to update to match existing and
                declared.
        """
        mask = []

        for attr in other.attributes:
            if other.attributes[attr] != self.attributes.get(attr, None):
                mask.append(attr)

        projects_ids = [ project['id'] for project in self.projects]

        mask.extend([p for p in other.projects if p['id'] not in projects_ids])

        return mask

def _build(org_id):
    try:
        TFC_TOKEN = getenv('TFC_TOKEN')
    except KeyError as e:
        raise KeyError('Empty TerraformCloud token') from e

    TFC_URL = getenv('TFC_URL', 'https://app.terraform.io')

    api = TFC(TFC_TOKEN, url=TFC_URL)
    api.set_org(org_id)

    return api

def _create_variable(org_id, varset_id, declared_variable):
    """
    Create a service account according to a declared one.

    Args:
        sa: ServiceAccount, the delcared service account.

    Returns:
        ServiceAccount, the service account created from the operation.
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

    result = _build(org_id).var_sets.add_var_to_varset(varset_id, body)

    print('Terraform Cloud variable created... ', end='')

    existing_variable.update_from_dict(result['data'])

    return existing_variable

def _update_variable(org_id, varset_id, declared_variable, existing_variable):
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

    result = _build(org_id).var_sets.update_var_in_varset(varset_id, existing_variable.id, body)

    existing_variable.update_from_dict(result['data'])

    print('variable updated... ', end='')

    return existing_variable

def _get_variable(org_id, varset_id, declared_variable):
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
    exists = False

    existing_variable = Variable(
        key=declared_variable.attributes['key']
    )

    variables = _build(org_id).var_sets.list_vars_in_varset(varset_id)

    for variable in variables.get('data', []):
        if variable['attributes']['key'] == declared_variable.attributes['key']:
            exists = True
            existing_variable.update_from_dict(variable)

    if not exists:
        raise IndexError(0)

    return existing_variable

def apply_variable(org_id, varset_id, key, value, category, sensitive=False,hcl=False, description=None):
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
    declared_variable = Variable(
        key=key,
        value=value,
        sensitive=sensitive,
        category=category,
        hcl=hcl,
        description=description
    )

    try:
        variable = _get_variable(org_id, varset_id, declared_variable)
    except IndexError as e:
        if e.args[0] == 0:
            variable = _create_variable(org_id, varset_id, declared_variable)
            
            return variable

    variable = _update_variable(org_id, varset_id, declared_variable, variable)

    return variable

def _create_variableset(org_id, declared_variableset):
    """
    Create a service account according to a declared one.

    Args:
        sa: ServiceAccount, the delcared service account.

    Returns:
        ServiceAccount, the service account created from the operation.
    """
    body = {
        "data": {
            "type": "varsets",
            "attributes": declared_variableset.attributes,
            "relationships": {
                "projects": {
                    "data": [
                        {
                            "id": project['id'],
                            "type": "projects"
                        } for project in declared_variableset.projects
                    ]
                }
            }
        }
    }

    existing_variableset = VariableSet(
        name=declared_variableset.attributes['name']
    )

    result = _build(org_id).var_sets.create(body)

    print('Terraform Cloud variableset created... ', end='')

    existing_variableset.update_from_dict(result['data'])

    return existing_variableset

def _update_variableset(org_id, declared_variableset, existing_variableset):
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
    mask = existing_variableset.diff(declared_variableset)

    # If there is non differences, return the original existing variable.
    if not mask:
        return existing_variableset

    body = {
        'data': {
            'type': 'varsets',
            'attributes': declared_variableset.attributes,
            'relationships': {
                'projects': {
                    'data': [
                        {
                            'id': project['id'],
                            'type': 'projects'
                        } for project in declared_variableset.projects if declared_variableset.projects
                    ]
                },
            }

        }
    }

    result = _build(org_id).var_sets.update(existing_variableset.id, body)

    existing_variableset.update_from_dict(result['data'])

    print('variable updated... ', end='')

    return existing_variableset

def _get_variableset(org_id, declared_variableset):
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
    exists = False

    existing_variableset = VariableSet(
        name=declared_variableset.attributes['name']
    )

    variablesets = _build(org_id).var_sets.list_all_for_org()

    for variableset in variablesets.get('data', []):
        if variableset['attributes']['name'] == declared_variableset.attributes['name']:
            exists = True
            existing_variableset.update_from_dict(variableset)

    if not exists:
        raise IndexError(0)

    return existing_variableset

def apply_variableset(org_id, name, description, project=None, glob=False):
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
    declared_variableset = VariableSet(
        name=name,
        description=description,
        project=project,
        glob=glob
    )

    try:
        variableset = _get_variableset(org_id, declared_variableset)
    except IndexError as e:
        if e.args[0] == 0:
            variableset = _create_variableset(org_id, declared_variableset)

    variableset = _update_variableset(org_id, declared_variableset, variableset)

    return variableset
