from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operation
from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2
from google.protobuf import field_mask_pb2

class TagKey:

    def __init__(self, parent, description, short_name):
        self.name = None
        self.namespace = parent.split('/')[1] + '/' + short_name
        self.data = {
            'description': description,
            'parent': parent,
            'shortName': short_name
        }
        self.iam_bindings = { 'bindings': [] }
    
    def create(self, credentials):
        """
        Create a tag key with google API call.

        Args:
            credentials: credentials, the user authentification to make a call.

        Returns:
            dict, the tag resulting from the operation.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            request = api.tagKeys().create(body=self.data)
            try:
                initial = request.execute()
            except HttpError as e:
                raise e
            result = operation.watch(api=api, operation=initial)
        if not 'response' in result:
            raise RuntimeError('the operation result did not contain any response. result: {0}'.format(str(result)))
        self.name = result['name']
        return None
    
    def update(self, credentials):
        """
        Update a tag key with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the tag resulting from the operation.
        
        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            update_request = api.tagKeys().patch(name=self.name, body=self.data)
            try:
                initial = update_request.execute()
            except HttpError as e:
                raise e
            result = operation.watch(api=api, operation=initial)
        return None
    
    def diff(self, credentials):
        """
        Show the differences between the declared tag key and and corresponding
            existing one.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the difference between declared and existing tag key, as a
                dict. If there is no existing state, returns None.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            # TODO: use a list parsing to find the tag key
            request = api.tagKeys().getNamespaced(name=self.namespace)
            try:
                result_tag = request.execute()
            except HttpError as e:
                if e.status_code != 403:
                    raise e
                return None
        self.name = result_tag['name']
        if result_tag['description'] != self.data['description']:
            return { 'description': self.data['description'] }
        return {}
    
    def access_control(self, credentials):
        """
        Apply IAM policy to the tag key.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the IAM policy applied.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            request = api.tagKeys().setIamPolicy(resource=self.name, body=self.iam_bindings)
            try:
                result_policy = request.execute()
            except HttpError as e:
                raise e
        return None

class WorkspaceTagKey(TagKey):

    def __init__(self, setup, builder_email):
        super().__init__(
            parent=setup['parent'],
            description=setup['workspaceTag']['description'],
            short_name=setup['workspaceTag']['shortName']
        )
        self.iam_bindings =  {
            'policy': {
                'bindings': [
                    {
                        'members': ['serviceAccount:{0}'.format(builder_email)],
                        'role': 'roles/resourcemanager.tagAdmin'
                    }
                ]
            }
        }
    
class RootTagValue:

    def __init__(self, setup, parent, namespace):
        self.name = None
        self.data = {
            'description': setup['trueValue']['description'],
            'parent': parent,
            'shortName': setup['trueValue']['shortName']
        }
        self.namespace = namespace + '/' + setup['trueValue']['shortName']

    def create(self, credentials):
        """
        Create a tag value with google API call.

        Args:
            credentials: credentials, the user authentification to make a call.

        Returns:
            dict, the tag value resulting from the operation.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            create_request = api.tagValues().create(body=self.data)
            try:
                initial = create_request.execute()
            except HttpError as e:
                raise e
            result = operation.watch(api=api, operation=initial)
        if not 'response' in result:
            raise RuntimeError('the operation result did not contain any response. result: {0}'.format(str(result)))
        self.name = result['name']
        return None

    def update(self, credentials):
        """
        Update a tag value with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the tag value resulting from the operation.
        
        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            update_request = api.tagValues().patch(name=self.name, body=self.data)
            try:
                initial = update_request.execute()
            except HttpError as e:
                raise e
            result = operation.watch(api=api, operation=initial)
        return None

    def diff(self, credentials):
        """
        Show the differences between the declared tag value and and
            corresponding existing one.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the difference between declared and existing tag value, as a
                dict. If there is no existing state, returns None.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            # TODO: use a list parsing to find the tag key
            request = api.tagValues().getNamespaced(name=self.namespace)
            try:
                result_value = request.execute()
            except HttpError as e:
                if e.status_code != 403:
                    raise e
                return None
        self.name = result_value['name']
        if result_value['description'] != self.data['description']:
            return { 'description': self.data['description'] }
        return {}

    def bind(self, credentials, project):
        """
        Bind the tag value to a project.

        Args:
            credentials: credential, the user authentification to make a call.
            project: string, the full resource name of the project. In of form:
                projects/123

        Returns:
            dict, the tagBinding created.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        body = {
            'parent': '//cloudresourcemanager.googleapis.com/{0}'.format(project),
            'tagValue': self.name
        }
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            request = api.tagBindings().create(body=body)        
            try:
                initial = request.execute()
            except HttpError as e:
                raise e
            result = operation.watch(api=api, operation=initial)
        return None

    def is_bound(self, credentials, project):
        """
        Indicate if the tag value is bound or not to a project.

        Args:
            credentials: credential, the user authentification to make a call.
            project: string, the full resource name of the project. In of form:
                projects/123

        Returns:
            bool, True if the project is bound to the tag value. False
                otherwise.
        """
        # build the api for resource management
        bindings = []
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            request = api.tagBindings().list(parent='//cloudresourcemanager.googleapis.com/{0}'.format(project))
            while request is not None:
                results = request.execute()
                if 'tagBindings' in results:
                    bindings.extend([ b['tagValue'] for b in results['tagBindings'] ])
                request = api.tagBindings().list_next(request, results)
        if self.name in bindings:
            return True
        return False

def create(key):
    """
    Create a tag key with google API call.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagKey, the delcared tag key.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the tag key created from
            the operation.
    """
    client = resourcemanager_v3.TagKeysClient()
    request = resourcemanager_v3.CreateTagKeyRequest(tag_key=key)
    operation = client.create_tag_key(request=request)
    response = operation.result()
    print('key created... ', end='')
    return response

def update(key, mask):
    """
    Update a tag key with google API call.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagKey, the delcared tag key.
        mask: string, a mask of entries to update to match the delcared tag key.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the tag key updated from
            the operation.
    """
    client = resourcemanager_v3.TagKeysClient()
    update_mask = field_mask_pb2.FieldMask(paths=mask)
    request = resourcemanager_v3.UpdateTagKeyRequest(
        tag_key=key,
        update_mask=update_mask
    )
    
    operation = client.update_tag_key(request=request)
    response = operation.result()
    print('key updated... ', end='')
    return response

def get(key):
    """
    Get the existing tag in Google organization corresponding to the definition.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagKey, the delcared tag key.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the existing tag key.

    Raises:
        ValueError, if there is no tag key matching the definition.
    """
    # this is the query to find the matching projects
    parent = key.parent
    existing = None

    # build the client for resource management
    client = resourcemanager_v3.TagKeysClient()
    request = resourcemanager_v3.ListTagKeysRequest(parent=parent)

    page_result = client.list_tag_keys(request=request)
    for result in page_result:
        if result.short_name == key.short_name:
            existing = result
    
    if existing is None:
        raise ValueError(0)
    
    return existing

def diff(declared, existing):
    """
    Get the existing tag in Google organization corresponding to the definition.

    Args:
        declared: [google.cloud.resourcemanager_v3.types.TagKey,
            google.cloud.resourcemanager_v3.types.TagValue] the delcared tag
            key or value.
        existing: [google.cloud.resourcemanager_v3.types.TagKey,
            google.cloud.resourcemanager_v3.types.TagValue] the existing tag
            key or value.

    Returns:
        list, the list of attributes to update to match existing and declared.
    """
    if existing.description == declared.description:
        return []
    
    return ['description']

def create_value(value):
    """
    Create a tag value with google API call.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagValue, the delcared tag
            value.

    Returns:
        google.cloud.resourcemanager_v3.types.TagValue, the tag value created
            from the operation.
    """
    client = resourcemanager_v3.TagValuesClient()
    request = resourcemanager_v3.CreateTagValueRequest(tag_value=value)
    operation = client.create_tag_value(request=request)
    response = operation.result()
    print('value created... ', end='')
    return response

def update_value(value, mask):
    """
    Update a tag value with google API call.

    Args:
        value: google.cloud.resourcemanager_v3.types.TagValue, the delcared tag
            value.
        mask: list, a mask of entries to update to match the delcared tag value.

    Returns:
        google.cloud.resourcemanager_v3.types.TagValue, the tag value updated
            from the operation.
    """
    client = resourcemanager_v3.TagValuesClient()
    update_mask = field_mask_pb2.FieldMask(paths=mask)
    request = resourcemanager_v3.UpdateTagValueRequest(
        tag_value=value,
        update_mask=update_mask
    )
    
    operation = client.update_tag_value(request=request)
    response = operation.result()
    print('value updated... ', end='')
    return response

def get_value(value):
    """
    Get the existing tag value in Google organization corresponding to the
        definition.

    Args:
        value: google.cloud.resourcemanager_v3.types.TagValue, the delcared tag
            value.

    Returns:
        google.cloud.resourcemanager_v3.types.TagValue, the existing tag value.

    Raises:
        ValueError, if there is no tag value matching the definition.
    """
    # this is the query to find the matching projects
    parent = value.parent
    existing = None

    # build the client for resource management
    client = resourcemanager_v3.TagValuesClient()
    request = resourcemanager_v3.ListTagValuesRequest(parent=parent)

    page_result = client.list_tag_values(request=request)
    for result in page_result:
        if result.short_name == value.short_name:
            existing = result
    
    if existing is None:
        raise ValueError(0)
    
    return existing

def generate_root_tag(setup):
    """
    Generate the root tag key and value. Can either create, update or leave it
        as it is. The tag is also updated with a new IAM policy.

    Args:
        setup: dict, the configuration used to build the root structure.

    Returns:
        google.cloud.resourcemanager_v3.types.TagValue, the generated tag value.
    """
    # Sets the variables for generating the tag
    declared_key = resourcemanager_v3.TagKey(
        parent=setup['parent'],
        short_name=setup['rootTag']['shortName'],
        description=setup['rootTag']['description'],
    )
    declared_value = resourcemanager_v3.TagValue(
        short_name=setup['trueValue']['shortName'],
        description=setup['trueValue']['description'],
    )

    try:
        key = get(declared_key)
    except ValueError as e:
        if e.args[0] == 0:
            key = create(declared_key)
    mask = diff(declared=declared_key, existing=key)
    if mask == []:
        print('key already exists... ', end='')
    else:
        key = update(declared_key, mask)

    declared_value.parent = key.name

    try:
        value = get_value(declared_value)
    except ValueError as e:
        if e.args[0] == 0:
            value = create_value(value)
    mask = diff(declared=declared_value, existing=value)
    if mask == []:
        print('value already exists... ', end='')
    else:
        value = update_value(declared_value, mask)    

    return value

def generate_workspace_tag(credentials, setup, builder_email):
    workspace_key = WorkspaceTagKey(setup=setup, builder_email=builder_email)
    diff = workspace_key.diff(credentials=credentials)
    if diff is None:
        workspace_key.create(credentials=credentials)
        print('tag key created... ', end='')
    elif diff != {}:
        workspace_key.update(credentials=credentials)
        print('tag key updated... ', end='')
    workspace_key.access_control(credentials=credentials)
    print('tag key is up-to-date.')
    return workspace_key