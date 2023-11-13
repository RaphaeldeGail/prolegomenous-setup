from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psetup import operations

root_tag_key_description = '''Use this tag to target a project that will be
used as a root project for the organization. Definition of a root project can
be found at https://github.com/RaphaeldeGail/prolegomenous-setup'''

true_tag_value_description = '''This value indicates that the project is a root
of the organization. It should be only used for project resources and should be
unique among an organization.'''

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
            create_request = api.tagKeys().create(body=self.data)
            try:
                operation = create_request.execute()
            except HttpError as e:
                raise e
            tag_key = operations.watch(api=api, operation=operation)
        self.name = tag_key['name']
        return tag_key
    
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
                operation = update_request.execute()
            except HttpError as e:
                raise e
            if ( not 'name' in operation ) and ( 'done' in operation ):
                return operation['response']
            tag_key = operations.watch(api=api, operation=operation)
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
        return result_policy

class RootTagKey(TagKey):

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            description=root_tag_key_description.replace('\n', ' '),
            short_name='root'
        )

class WorkspaceTagKey(TagKey):

    def __init__(self, parent, builder_email):
        super().__init__(
            parent=parent,
            description='Name of the workspace',
            short_name='workspace'
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

    def __init__(self,parent, namespace):
        self.name = None
        self.data = {
            'description': true_tag_value_description.replace('\n', ' '),
            'parent': parent,
            'shortName': 'true'
        }
        self.namespace = namespace + '/true'

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
                operation = create_request.execute()
            except HttpError as e:
                raise e
            tag_value = operations.watch(api=api, operation=operation)
        self.name = tag_value['name']
        return tag_value

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
                operation = update_request.execute()
            except HttpError as e:
                raise e
            if ( not 'name' in operation ) and ( 'done' in operation ):
                return operation['response']
            tag_value = operations.watch(api=api, operation=operation)
        return tag_value

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
                operation = request.execute()
            except HttpError as e:
                raise e
            if ( not 'name' in operation ) and ( 'done' in operation ):
                return operation['response']
            tag_binding = operations.watch(api=api, operation=operation)
        return tag_binding

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

def generate_root_tag(credentials, parent):
    root_key = RootTagKey(parent=parent)
    diff = root_key.diff(credentials=credentials)
    if diff is None:
        root_key.create(credentials=credentials)
        print('tag key created... ', end='')
    elif diff != {}:
        root_key.update(credentials=credentials)
        print('tag key updated... ', end='')
    true_value = RootTagValue(parent=root_key.name, namespace=root_key.namespace)
    diff = true_value.diff(credentials=credentials)
    if diff is None:
        true_value.create(credentials=credentials)
        print('tag value created... ', end='')
    elif diff != {}:
        true_value.update(credentials=credentials)
        print('tag value updated... ', end='')
    print('tag value is up-to-date.')
    return true_value

def generate_workspace_tag(credentials, parent, builder_email):
    workspace_key = WorkspaceTagKey(parent=parent, builder_email=builder_email)
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