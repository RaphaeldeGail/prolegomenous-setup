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
    
    # TODO: use try/except to wrap api calls
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
            create_request = api.tagKeys().create(body=self.data)
            operation = create_request.execute()
            tag_key = operations.watch(api=api, name=operation['name'])
        return tag_key
    
    def update(self, credentials):
        """
        Update a tag key with google API call.

        Args:
            credentials: credential, the user authentification to make a call.

        Returns:
            dict, the tag resulting from the operation.
        """
        # build the api for resource management
        with build('cloudresourcemanager', 'v3', credentials=credentials) as api:
            update_request = api.tagKeys().patch(name=self.name, body=self.data)
            operation = update_request.execute()
            tag_key = operations.watch(api=api, name=operation['name'])
        return tag_key
    
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
        spec = self.data
        namespace = spec['parent'].split('/')[1] + '/' + spec['shortName']
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
        if result_tag['description'] != spec['description']:
            return { 'description': spec['description'] }
        return {}
    
    def access_control(self, credentials):
        for member in self.iam_bindings['members']:
            print(member)
        return None

class RootTagKey(TagKey):

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            description='''
Use this tag to target a project that will be used as a root
project for the organization. Definition of a root project can
be found at
https://github.com/RaphaeldeGail/prolegomenous-setup
            ''',
            short_name='root'
        )

class WorkspaceTagKey(TagKey):

    def __init__(self, parent, builder_group):
        super().__init__(
            parent=parent,
            description='Name of the workspace',
            short_name='workspace'
        )
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
    diff = root_key.diff(credentials=credentials)
    if diff is None:
        root_key.create(credentials=credentials)
        print('tag key created... ', end='')
    if diff != {}:
        root_key.update(credentials=credentials)
        print('tag key updated... ', end='')
    true_value = RootTagValue(parent=root_key.name)
    print(true_value.data)
    if true_value.clear(credentials=credentials) is None:
        print('clear')
    workspace_key = WorkspaceTagKey(parent=parent, builder_group='yo')
    print(workspace_key.data)
    workspace_key.access_control(credentials=credentials)
    return true_value