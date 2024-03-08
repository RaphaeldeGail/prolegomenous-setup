"""Generate a tag key idempotently.

Can apply a specific configuration for a tag key and create or update it in
order to match the configuration. The tag key IAM policy can also be updated
with this module.

Typical usage example:

    my_key = tag.apply('parent', 'myName', 'description')

    tag.control(my_key, {keyPolicy})
"""

from google.cloud.resourcemanager_v3 import (
    TagKey,
    TagKeysClient,
    CreateTagKeyRequest,
    UpdateTagKeyRequest,
    ListTagKeysRequest
)
from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest
from google.protobuf.field_mask_pb2 import FieldMask

def _create(key):
    """
    Create a tag key according to to a resource declaration.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagKey, the delcared
            resource.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the tag key created from
            the operation.
    """
    client = TagKeysClient()
    request = CreateTagKeyRequest(tag_key=key)

    operation = client.create_tag_key(request=request)
    response = operation.result()

    print('... key created... ')

    return response

def _update(declared_key, existing_key):
    """
    Update a tag key according to a resource declaration.

    Args:
        declared_key: google.cloud.resourcemanager_v3.types.TagKey, the
            declared resource.
        existing_key: google.cloud.resourcemanager_v3.types.TagKey, the
            existing resource.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the tag key updated by
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

    print('... key updated... ')

    return response

def _get(key):
    """Get the existing tag key corresponding to the declared resource.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagKey, the delcared
            resource.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the existing tag key.

    Raises:
        IndexError, matching tag key amount to 0.
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
        raise IndexError(0)

    return existing

def _diff(declared, existing):
    """
    Show the differences between a tag key and a declared one.

    Args:
        declared: google.cloud.resourcemanager_v3.types.TagKey, the delcared
            resource.
        existing: google.cloud.resourcemanager_v3.types.TagKey, the existing
            resource.

    Returns:
        list, the list of attributes to update to match existing and declared.
    """
    if existing.description == declared.description:
        return []

    return ['description']

def control(key, policy):
    """
    Apply IAM policy to the tag key.

    Args:
        key: google.cloud.resourcemanager_v3.types.TagKey, the delcared
            resource.
        policy: google.iam.v1.policy_pb2.Policy, the policy to apply.
    """
    client = TagKeysClient()
    request = SetIamPolicyRequest(
        resource=key.name,
        policy=policy
    )

    client.set_iam_policy(request=request)

    return None

def apply(parent, shortName, description):
    """Generate a tag key.

    Can either create, update or leave it as it is.

    Args:
        parent: string, the name of the organization hosting the tag key.
        shortName: string, a user-friendly name for the tag key.
        description: string, a description of the yag key.

    Returns:
        google.cloud.resourcemanager_v3.types.TagKey, the tag key generated
            according to the declaration.
    """
    declared_key = TagKey(
        parent=parent,
        short_name=shortName,
        description=description,
    )

    try:
        key = _get(declared_key)
    except IndexError as e:
        if e.args[0] == 0:
            key = _create(declared_key)

    key = _update(declared_key, key)

    return key
