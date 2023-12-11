from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2

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
    client = resourcemanager_v3.FoldersClient()
    request = resourcemanager_v3.CreateFolderRequest(folder=folder)

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

    client = resourcemanager_v3.FoldersClient()
    request = resourcemanager_v3.ListFoldersRequest(parent=folder.parent)

    page_result = client.list_folders(request=request)

    for response in page_result:
        if folder.display_name == response.display_name:
            existing = response

    if existing is None:
        raise ValueError(0)
    
    return existing

def _control_access(folder, policy):
    """
    Apply IAM policy to the folder.

    Args:
        folder: google.cloud.resourcemanager_v3.types.Folder, the delcared
            folder.
        policy: dict, list all `bindings` to apply to the folder policy.
    """
    client = resourcemanager_v3.FoldersClient()
    request = iam_policy_pb2.SetIamPolicyRequest(
        resource=folder.name,
        policy=policy
    )

    client.set_iam_policy(request=request)

    print('IAM policy set... ', end='')

    return None

def generate_folder(setup, builder_email):
    """
    Generate the workspaces folder. Can either create, update or leave it as it
        is. The folder is also updated with a new IAM policy.

    Args:
        setup: dict, the configuration used to build the root structure.
        builder_email: string, the email of the builder service account.

    Returns:
        google.cloud.resourcemanager_v3.types.Folder, the generated folder.
    """
    exec_gr = 'group:{0}'.format(setup['google']['groups']['executive_group'])
    builder_role = setup['workspaceFolder']['builderRole']
    full_role_name = '{0}/roles/{1}'.format(setup['parent'], builder_role)
    policy = {
        'bindings': [
            {
                'members': [ exec_gr ],
                'role': 'roles/resourcemanager.folderAdmin'
            },
            {
                'members': ['serviceAccount:{0}'.format(builder_email)],
                'role': full_role_name
            }
        ]
    }

    declared_folder = resourcemanager_v3.Project(
        parent=setup['parent'],
        display_name=setup['workspaceFolder']['displayName']
    )

    try:
        folder = _get_folder(declared_folder)
    except ValueError as e:
        if e.args[0] == 0:
            folder = _create_folder(declared_folder)

    _control_access(folder=folder, policy=policy)

    return folder