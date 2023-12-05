from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2
from google.protobuf import field_mask_pb2

def _create_key(key):
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

def _update_key(declared_key, existing_key):
    """
    Update a tag key with google API call.

    Args:
        declared_key: google.cloud.resourcemanager_v3.types.TagKey, the
            declared tag key.
        existing_key: google.cloud.resourcemanager_v3.types.TagKey, the
            existing tag key.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the tag key updated from
            the operation.
    """
    mask = _diff(declared=declared_key, existing=existing_key)

    if mask == []:
        return existing_key
    
    client = resourcemanager_v3.TagKeysClient()
    update_mask = field_mask_pb2.FieldMask(paths=mask)
    request = resourcemanager_v3.UpdateTagKeyRequest(
        tag_key=declared_key,
        update_mask=update_mask
    )
    
    operation = client.update_tag_key(request=request)
    response = operation.result()
    print('key updated... ', end='')
    return response

def _get_key(key):
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

def _diff(declared, existing):
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

def _create_value(value):
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

def _update_value(declared_value, existing_value):
    """
    Update a tag value with google API call.

    Args:
        declared_value: google.cloud.resourcemanager_v3.types.TagValue, the
            declared tag value.
        existing_value: google.cloud.resourcemanager_v3.types.TagValue, the
            existing tag value.

    Returns:
        google.cloud.resourcemanager_v3.types.TagValue, the tag value updated
            from the operation.
    """
    mask = _diff(declared=declared_value, existing=existing_value)

    if mask == []:
        return existing_value

    client = resourcemanager_v3.TagValuesClient()
    update_mask = field_mask_pb2.FieldMask(paths=mask)
    request = resourcemanager_v3.UpdateTagValueRequest(
        tag_value=declared_value,
        update_mask=update_mask
    )
    
    operation = client.update_tag_value(request=request)
    response = operation.result()
    print('value updated... ', end='')
    return response

def _get_value(value):
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

def _is_bound(binding):
    """
    Indicate if the tag value is bound or not to a project.

    Args:
        binding: google.cloud.resourcemanager_v3.types.TagBinding, the delcared
            tag binding.

    Returns:
        bool, True if the project is bound to the tag value. False
            otherwise.
    """
    client = resourcemanager_v3.TagBindingsClient()
    request = resourcemanager_v3.ListTagBindingsRequest(
        parent=binding.parent
    )

    page_result = client.list_tag_bindings(request=request)

    for response in page_result:
        if binding.tag_value == response.tag_value:
            return True
    return False

def _bind(binding):
    """
    Bind the tag value to a project.

    Args:
        binding: google.cloud.resourcemanager_v3.types.TagBinding, the delcared
            tag binding.

    Returns:
        google.cloud.resourcemanager_v3.types.TagBinding, the tag binding
            created.
    """
    if _is_bound(binding=binding):
        return binding

    client = resourcemanager_v3.TagBindingsClient()
    request = resourcemanager_v3.CreateTagBindingRequest(tag_binding=binding)
    operation = client.create_tag_binding(request=request)

    response = operation.result()
    print('binding created... ', end='')

    return response

def _control_access(key, policy):
    """
    Apply IAM policy to the project.

    Args:
        project: google.cloud.resourcemanager_v3.types.Project, the delcared
            project.
        policy: dict, list all `bindings` to apply to the project policy.
    """
    client = resourcemanager_v3.TagKeysClient()
    request = iam_policy_pb2.SetIamPolicyRequest(
        resource=key.name,
        policy=policy
    )

    client.set_iam_policy(request=request)

    return None    

def generate_root_tag(setup, project):
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
    declared_binding = resourcemanager_v3.TagBinding(
        parent='//cloudresourcemanager.googleapis.com/{0}'.format(project.name)
    )

    try:
        key = _get_key(declared_key)
    except ValueError as e:
        if e.args[0] == 0:
            key = _create_key(declared_key)
    key = _update_key(declared_key, key)

    declared_value.parent = key.name

    try:
        value = _get_value(declared_value)
    except ValueError as e:
        if e.args[0] == 0:
            value = _create_value(value)
    value = _update_value(declared_value, value)

    declared_binding.tag_value = value.name 

    _bind(binding=declared_binding)

    return value

def generate_workspace_tag(setup, builder_email):
    # Sets the variables for generating the tag
    account = 'serviceAccount:{0}'.format(builder_email)
    role = 'roles/resourcemanager.tagAdmin'
    policy = {'bindings': [{'members': [account],'role': role}]}

    declared_key = resourcemanager_v3.TagKey(
        parent=setup['parent'],
        short_name=setup['workspaceTag']['shortName'],
        description=setup['workspaceTag']['description'],
    )
    try:
        key = _get_key(declared_key)
    except ValueError as e:
        if e.args[0] == 0:
            key = _create_key(declared_key)
    key = _update_key(declared_key, key)

    _control_access(key=key, policy=policy)
    print('IAM policy set... ', end='')
    return key