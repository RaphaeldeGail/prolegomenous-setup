class IamPolicy():
    """A class to represent a service account in Google Cloud project.

    Attributes:
        account_id: string, the ID for the service account, which becomes the
            final component of the resource name.
        description: string, a description of the service account.
        display_name: string, a user-friendly name for the service account.
        project: string, the ID of the project to create this account in.

    """

    def __init__(self, bindings=None):
        # Initial empty `bindings` list
        self.bindings = {}

        if bindings:
            for binding in bindings:
                if not binding['role'] in self.bindings:
                    self.bindings.update({binding['role']: binding['members']})
                else:
                    self.bindings[binding['role']].extend(binding['members'])

    @property
    def format(self):
        fmt = {
            'bindings': [
                {
                    'role': role,
                    'members': members
                } for role, members in self.bindings.items()
            ]
        }
        return fmt

    def add(self, binding):
        if not binding['role'] in self.bindings:
            self.bindings.update({binding['role']: binding['members']})
        else:
            self.bindings[binding['role']].extend(binding['members'])

def organization(setup, executive_role):
    prefix = 'roles/resourcemanager.organization'
    adm_grp = f'group:{setup["googleGroups"]["admins"]}'
    exec_grp = f'group:{setup["googleGroups"]["executive"]}'
    fin_grp = f'group:{setup["googleGroups"]["finops"]}'
    pol_grp = f'group:{setup["googleGroups"]["policy"]}'
    owner = f'user:{setup["owner"]}'
    iam = [
        { 'role': executive_role.name, 'members': [ exec_grp ] },
        { 'role': 'roles/billing.admin', 'members': [ fin_grp ] },
        { 'role': 'roles/essentialcontacts.admin', 'members': [ owner ] },
        { 'role': 'roles/iam.organizationRoleAdmin', 'members': [ adm_grp ] },
        { 'role': 'roles/orgpolicy.policyAdmin', 'members': [ pol_grp ] },
        { 'role': f'{prefix}Admin', 'members': [ adm_grp, owner ] },
        { 'role': f'{prefix}Viewer', 'members': [ fin_grp, pol_grp ] }
    ]

    return IamPolicy(iam)

def project(setup):
    iam = [{
        'role': 'roles/owner',
        'members': [ f'group:{setup["googleGroups"]["executive"]}' ]
    }]

    return IamPolicy(iam)

def account(setup, pool, tfc_project):
    prefix = f'principalSet://iam.googleapis.com/{pool.name}'
    principal = f'{prefix}/attribute.terraform_project_id/{tfc_project.id}'
    iam = [
        {
            'role': 'roles/iam.serviceAccountTokenCreator',
            'members': [ f'group:{setup["googleGroups"]["executive"]}' ]
        },
        {
            'role': 'roles/iam.workloadIdentityUser',
            'members': [ principal ]
        }
    ]

    return IamPolicy(iam)

def workspace_tag(account):
    builder_email = f'serviceAccount:{account.email}'
    iam = [{
        'role': 'roles/resourcemanager.tagAdmin',
        'members': [ builder_email ]
    }]

    return IamPolicy(iam)

def workspace_folder(setup, account):
    org = setup['googleOrganization']['name']
    builder_role = f'{org}/roles/{setup["builderRole"]["name"]}'
    builder_email = f'serviceAccount:{account.email}'
    iam = [{
        'role': 'roles/resourcemanager.folderAdmin',
        'members': [ f'group:{setup["googleGroups"]["executive"]}' ]
    },
    {
        'role': builder_role,
        'members': [ builder_email ]
    }]

    return IamPolicy(iam)

def billing_account(email):
    mail = f'serviceAccount:{email}'
    iam = [
        {'members': [ mail ], 'role': 'roles/billing.user'},
        {'members': [ mail ], 'role': 'roles/billing.costsManager'},
        {'members': [ mail ], 'role': 'roles/iam.securityAdmin'}
    ]

    return IamPolicy(iam)
