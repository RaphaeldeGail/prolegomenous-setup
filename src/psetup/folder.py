from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operation

class WorkspaceFolder:

    display_name = 'Workspaces'

    def __init__(self, parent, executive_group, builder_email):
        self.name = None
        self.data = {
            'displayName': self.display_name,
            'parent': parent,
        }
        self.iam_bindings = {
            'policy': {
                'bindings': [
                    {
                        'members': ['group:{0}'.format(executive_group)],
                        'role': 'roles/resourcemanager.folderAdmin'
                    },
                    {
                        'members': ['serviceAccount:{0}'.format(builder_email)],
                        'role': '{0}/roles/workspaceBuilder'.format(parent)
                    }
                ]
            }
        }

    def create(self, credentials):
        """
        Create a folder with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the folder resulting from the operation.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            request = api.folders().create(body=self.data)
            initial = request.execute()
            result = operation.watch(api=api, operation=initial)
        if not 'response' in result:
            raise RuntimeError('the operation result did not contain any response. result: {0}'.format(str(result)))
        self.name = result['response']['name']
        return result['response']

    def diff(self, credentials):
        """
        Show the differences between the declared folder and and corresponding
            existing folder.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the difference between declared and existing folder, as a
                dict. If there is no existing state, returns None.
        """
        # this is the query to find the matching folders
        query = (
            'parent={0}'.format(self.data['parent']),
            ' AND displayName={0}'.format(self.display_name),
            ' AND state=ACTIVE'
        )
        # build the api for resource management
        folders = []
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            # Look for a folder that already matches the declaration
            request = api.folders().search(query=''.join(query))
            while request is not None:
                results = request.execute()
                if 'folders' in results:
                    folders.extend([ f for f in results['folders'] ])
                request = api.folders().search_next(request, results)
        if folders == []:
            return None
        if len(folders) == 1:
            self.name = folders[0]['name']
            return folders[0]
        if len(folders) > 1:
            raise RuntimeError('There should be at most one folder with displayName "Workspaces" in the organization. found: {0}'.format(len(folders)))

    def access_control(self, credentials):
        """
        Apply IAM policy to the folder.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the IAM policy applied.

        Raises:
            HttpError, Raises an exception if the API call does not return a
                successful HTTP response.
        """
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            request = api.folders().setIamPolicy(resource=self.name, body=self.iam_bindings)
            try:
                result = request.execute()
            except HttpError as e:
                raise e
        return result

def generate_folder(credentials, parent, executive_group, builder_email):
    """
    Generate the root project and related resources.

    Args:
        credentials: credential, the user authentification to make a call.
        parent: string, the name of the organisation hosting the project.
        executive_group: string, the email address of the group for executives
            for the organization.
        builder_email: string, the email address of the builder service
            account.

    Returns:
        WorkspaceFolder, the project created.
    """
    folder = WorkspaceFolder(
        parent=parent,
        executive_group=executive_group,
        builder_email=builder_email
    )
    diff = folder.diff(credentials=credentials)
    if diff is None:
        folder.create(credentials=credentials)
        print('folder created... ', end='')
    folder.access_control(credentials=credentials)
    print('IAM policies set... ', end='')
    print('folder is up-to-date.')
    return folder