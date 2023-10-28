from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operations

class TagKey:

    def __init__(self, parent, description, short_name):
        self.name = None
        self.data = {
            'description': description,
            'parent': parent,
            'shortName': short_name
        }
        self.iam_bindings = { 'members': [] }
    
    def create(self, credentials):
        """
        Create a tag key with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the tag resulting from the operation.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            return None
        return None
    
    def update(self, credentials):
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
        """
        declared = self.data
        namespace = '{parent}/{name}'.format(parent=declared['parent'].split('/')[1], name=declared['shortName'])
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            # TODO: use a list parsing to find the tag key
            request = api.tagKeys().getNamespaced(name=namespace)
            try:
                result_tag = request.execute()
            except HttpError as e:
                if e.status_code != 403:
                    raise e
                return None
        self.name = result_tag['name']
        if result_tag['description'] != declared['description']:
            return { 'description': declared['description'] }
        return {}
    
    def access_control(self, credentials):
        for member in self.iam_bindings['members']:
            print(member)
        return None

class RootTagKey(TagKey):

    def __init__(self, parent):
        super().__init__(parent=parent, description='Root project of an organization', short_name='root')

class WorkspaceTagKey(TagKey):

    def __init__(self, parent, builder_group):
        super().__init__(parent=parent, description='Workspace name', short_name='workspace')
        self.iam_bindings['members'] = [
            {
                'serviceAccount': builder_group,
                'role': 'roles/resourcemanager.tagAdmin'
            }
        ]
    
class RootTagValue:

    def __init__(self,parent):
        self.name = None
        self.data = {
            'description': 'If the project is a root of an organization',
            'parent': parent,
            'shortName': 'true'
        }

    def create(self, credentials):
        return None

    def update(self, credentials):
        return None

    def diff(self, credentials):
        return None

    def clear(self, credentials):
        """
        Remove any binding from tag value.
        """
        return None

    def bind(self, credentials, project):
        """
        Bind the tag value to a project.
        """
        return None

def generate_tags(credentials, parent):
    print(parent)
    root_key = RootTagKey(parent=parent)
    print(root_key.data)
    print(root_key.diff(credentials=credentials))
    true_value = RootTagValue(parent=root_key.name)
    print(true_value.data)
    if true_value.clear(credentials=credentials) is None:
        print('clear')
    workspace_key = WorkspaceTagKey(parent=parent, builder_group='yo')
    print(workspace_key.data)
    workspace_key.access_control(credentials=credentials)
    return true_value