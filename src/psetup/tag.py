"""Generate a tag key and value idempotently.

Can apply a specific configuration for a tag and create or update it in
order to match the configuration.

Typical usage example:

  generate_root_tag(setup, project)
  generate_workspace_tag(setup, builder_email)
"""

from google.cloud.resourcemanager_v3 import (
    TagKey,
    TagKeysClient,
    CreateTagKeyRequest,
    UpdateTagKeyRequest,
    ListTagKeysRequest,
    TagValuesClient,
    CreateTagValueRequest,
    UpdateTagValueRequest,
    ListTagValuesRequest,
    TagBindingsClient,
    ListTagBindingsRequest,
    CreateTagBindingRequest
)
from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest
from google.protobuf.field_mask_pb2 import FieldMask

from .utils import IamPolicy

def _create_key(key):
    """
    Create a tag key according to a declared key.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagKey, the delcared tag key.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the tag key created from
            the operation.
    """
    client = TagKeysClient()
    request = CreateTagKeyRequest(tag_key=key)

    operation = client.create_tag_key(request=request)
    response = operation.result()

    print('key created... ', end='')

    return response

def _update_key(declared_key, existing_key):
    """
    Update an existing tag key compared to a declared key.

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

    # If there is non differences, return the original existing key.
    if not mask:
        return existing_key

    client = TagKeysClient()
    update_mask = FieldMask(paths=mask)
    request = UpdateTagKeyRequest(
        tag_key=declared_key,
        update_mask=update_mask
    )

    operation = client.update_tag_key(request=request)
    response = operation.result()

    print('key updated... ', end='')

    return response

def _get_key(key):
    """
    Get the existing tag in Google organization corresponding to the declared
        tag key.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagKey, the delcared tag key.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the existing tag key.

    Raises:
        ValueError, if there is no tag key matching the definition.
    """
    parent = key.parent
    existing = None

    client = TagKeysClient()
    request = ListTagKeysRequest(parent=parent)

    page_result = client.list_tag_keys(request=request)

    for result in page_result:
        if result.short_name == key.short_name:
            existing = result

    if existing is None:
        raise ValueError(0)

    return existing

def _diff(declared, existing):
    """
    Show the differences between a declared and an existing tag key or value.

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
    Create a tag value according to a declared value.

    Args:
        value: google.cloud.resourcemanager_v3.types.TagValue, the delcared tag
            value.

    Returns:
        google.cloud.resourcemanager_v3.types.TagValue, the tag value created
            from the operation.
    """
    client = TagValuesClient()
    request = CreateTagValueRequest(tag_value=value)

    operation = client.create_tag_value(request=request)
    response = operation.result()

    print('value created... ', end='')

    return response

def _update_value(declared_value, existing_value):
    """
    Update an existing tag value compared to a declared value.

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

    # If there is non differences, return the original existing value.
    if not mask:
        return existing_value

    client = TagValuesClient()
    update_mask = FieldMask(paths=mask)
    request = UpdateTagValueRequest(
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
    parent = value.parent
    existing = None

    client = TagValuesClient()
    request = ListTagValuesRequest(parent=parent)

    page_result = client.list_tag_values(request=request)

    for result in page_result:
        if result.short_name == value.short_name:
            existing = result

    if existing is None:
        raise ValueError(0)

    return existing

def _get_binding(binding):
    """
    Get the existing tag binding in project corresponding to the definition.

    Args:
        binding: google.cloud.resourcemanager_v3.types.TagBinding, the delcared
            tag binding.

    Returns:
        binding: google.cloud.resourcemanager_v3.types.TagBinding, the existing
            tag binding.

    Raises:
        ValueError, if there is no tag binding matching the definition.
    """
    existing = None

    client = TagBindingsClient()
    request = ListTagBindingsRequest(
        parent=binding.parent
    )

    page_result = client.list_tag_bindings(request=request)

    for response in page_result:
        if binding.tag_value == response.tag_value:
            existing = response

    if existing is None:
        raise ValueError(0)

    return existing

def _create_binding(binding):
    """
    Bind the tag value to a project.

    Args:
        binding: google.cloud.resourcemanager_v3.types.TagBinding, the delcared
            tag binding.

    Returns:
        google.cloud.resourcemanager_v3.types.TagBinding, the tag binding
            created.
    """
    client = TagBindingsClient()
    request = CreateTagBindingRequest(tag_binding=binding)

    operation = client.create_tag_binding(request=request)
    response = operation.result()

    print('binding created... ', end='')

    return response

def control_access(key, policy):
    """
    Apply IAM policy to the tag key.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagKey, the delcared tag key.
        policy: dict, list all `bindings` to apply to the tag policy.
    """
    client = TagKeysClient()
    request = SetIamPolicyRequest(
        resource=key.name,
        policy=IamPolicy(policy).policy
    )

    client.set_iam_policy(request=request)

    return None

def apply_key(parent, short_name, description):
    """
    Generate the root tag key and value. Can either create, update or leave it
        as it is. The tag value is also updated with a binding.

    Args:
        setup: dict, the configuration used to build the root structure.
        project: string, the name of the project to bind the tag value with.

    Returns:
        google.cloud.resourcemanager_v3.types.TagValue, the generated tag value.
    """
    declared_key = TagKey(
        parent=parent,
        short_name=short_name,
        description=description,
    )

    try:
        key = _get_key(declared_key)
    except IndexError as e:
        if e.args[0] == 0:
            key = _create_key(declared_key)

    key = _update_key(declared_key, key)

    return key

def apply_value(declared_value):
    """
    Generate the root tag key and value. Can either create, update or leave it
        as it is. The tag value is also updated with a binding.

    Args:
        setup: dict, the configuration used to build the root structure.
        project: string, the name of the project to bind the tag value with.

    Returns:
        google.cloud.resourcemanager_v3.types.TagValue, the generated tag value.
    """
    try:
        value = _get_value(declared_value)
    except IndexError as e:
        if e.args[0] == 0:
            value = _create_value(value)

    value = _update_value(declared_value, value)

    return value

def apply_binding(declared_binding):
    """
    Generate the root tag key and value. Can either create, update or leave it
        as it is. The tag value is also updated with a binding.

    Args:
        setup: dict, the configuration used to build the root structure.
        project: string, the name of the project to bind the tag value with.

    Returns:
        google.cloud.resourcemanager_v3.types.TagValue, the generated tag value.
    """
    try:
        binding = _get_binding(declared_binding)
    except IndexError as e:
        if e.args[0] == 0:
            binding = _create_binding(declared_binding)

    return binding
