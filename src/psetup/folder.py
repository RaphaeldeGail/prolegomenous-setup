"""Generate a folder idempotently.

Can apply a specific configuration for a folder and create or update it in
order to match the configuration.

Typical usage example:

  folder = generate_folder(setup, builder_email)
"""

from google.cloud.resourcemanager_v3 import (
    FoldersClient,
    CreateFolderRequest,
    ListFoldersRequest
)
from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest

def _create_folder(folder):
    """
    Create a folder according to a declared folder.

    Args:
        folder: google.cloud.resourcemanager_v3.types.Folder, the declared
            folder.

    Returns:
        google.cloud.resourcemanager_v3.types.Folder, the folder created from
            the operation.
    """
    client = FoldersClient()
    request = CreateFolderRequest(folder=folder)

    operation = client.create_project(request=request)
    response = operation.result()

    print('folder created... ', end='')

    return response

def _get_folder(folder):
    """
    Get the existing folder in Google organization corresponding to the
        declared folder.

    Args:
        folder: google.cloud.resourcemanager_v3.types.Folder, the delcared
            folder.

    Returns:
        google.cloud.resourcemanager_v3.types.Folder, the existing folder if
            it exists.

    Raises:
        ValueError, if there is no folder matching the declared folder.
    """
    existing = None

    client = FoldersClient()
    request = ListFoldersRequest(parent=folder.parent)

    page_result = client.list_folders(request=request)

    for response in page_result:
        if folder.display_name == response.display_name:
            existing = response

    if existing is None:
        raise IndexError(0)

    return existing

def control_access(folder, policy):
    """
    Apply IAM policy to the folder.

    Args:
        folder: google.cloud.resourcemanager_v3.types.Folder, the delcared
            folder.
        policy: dict, list all `bindings` to apply to the folder policy.
    """
    client = FoldersClient()
    request = SetIamPolicyRequest(
        resource=folder.name,
        policy=policy.policy
    )

    client.set_iam_policy(request=request)

    return None

def apply_folder(declared_folder):
    """
    Generate the workspaces folder. Can either create, update or leave it as it
        is. The folder is also updated with a new IAM policy.

    Args:
        setup: dict, the configuration used to build the root structure.
        builder_email: string, the email of the builder service account.

    Returns:
        google.cloud.resourcemanager_v3.types.Folder, the generated folder.
    """
    try:
        folder = _get_folder(declared_folder)
    except IndexError as e:
        if e.args[0] == 0:
            folder = _create_folder(declared_folder)

    return folder
