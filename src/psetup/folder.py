"""Generate a folder idempotently.

Can apply a specific configuration for a folder and create or update it in
order to match the configuration. The folder IAM policy can also be updated
with this module.

Typical usage example:

  folder = folder.apply_folder(parent='folderParent', displayName='folderName')

  folder.control_access(folder, policy={folderPolicy})
"""

from google.cloud.resourcemanager_v3 import (
    Folder,
    FoldersClient,
    CreateFolderRequest,
    ListFoldersRequest
)
from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest

def _create(folder):
    """Create a folder according to a resource declaration.

    Args:
        folder: google.cloud.resourcemanager_v3.types.Folder, the declared
            resource.

    Returns:
        google.cloud.resourcemanager_v3.types.Folder, the folder created from
            the operation.
    """
    client = FoldersClient()
    request = CreateFolderRequest(folder=folder)

    operation = client.create_folder(request=request)
    response = operation.result()

    print('... folder created... ')

    return response

def _get(folder):
    """Get the existing folder corresponding to the declared resource.

    Args:
        folder: google.cloud.resourcemanager_v3.types.Folder, the delcared
            resource.

    Returns:
        google.cloud.resourcemanager_v3.types.Folder, the existing folder if
            it exists.

    Raises:
        IndexError, matching folders amount to 0.
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

def control(folder, policy):
    """Apply IAM policy to the folder.

    Args:
        folder: google.cloud.resourcemanager_v3.types.Folder, the delcared
            resource.
        policy: google.iam.v1.policy_pb2.Policy, the policy to apply.
    """
    client = FoldersClient()
    request = SetIamPolicyRequest(
        resource=folder.name,
        policy=policy
    )

    client.set_iam_policy(request=request)

    return None

def apply(parent, displayName):
    """Generate the workspaces folder.
    
    Can either create, update or leave it as it is.

    Args:
        parent: string, the name of the parent hosting the folder.
        displayName: string, the user-friendly name of the folder.

    Returns:
        google.cloud.resourcemanager_v3.types.Folder, the folder generated
            according to the declaration.
    """
    declared_folder = Folder(
        parent=parent,
        display_name=displayName
    )

    try:
        folder = _get(declared_folder)
    except IndexError as e:
        if e.args[0] == 0:
            folder = _create(declared_folder)

    return folder
