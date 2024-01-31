from google.iam.v1.policy_pb2 import Policy

def organization(setup):
    prefix = 'roles/resourcemanager.organization'
    adm_grp = f'group:{setup["googleGroups"]["admins"]}'
    fin_grp = f'group:{setup["googleGroups"]["finops"]}'
    pol_grp = f'group:{setup["googleGroups"]["policy"]}'
    owner = f'user:{setup["owner"]}'

    iam = Policy()
    iam.bindings.add(role='roles/billing.admin', members=[ fin_grp ])
    iam.bindings.add(role='roles/iam.organizationRoleAdmin', members=[ adm_grp ])
    iam.bindings.add(role='roles/orgpolicy.policyAdmin', members=[ pol_grp ])
    iam.bindings.add(role=f'{prefix}Admin', members=[ adm_grp, owner ])
    iam.bindings.add(role=f'{prefix}Viewer', members=[ fin_grp, pol_grp ])

    return iam

def project(setup):
    executives = f'group:{setup["googleGroups"]["executive"]}'

    iam = Policy()
    iam.bindings.add(role='roles/owner', members=[ executives ])

    return iam

def account(setup, pool, tfc_project):
    prefix = f'principalSet://iam.googleapis.com/{pool.name}'
    principal = f'{prefix}/attribute.terraform_project_id/{tfc_project}'
    executives = f'group:{setup["googleGroups"]["executive"]}'

    iam = Policy()
    iam.bindings.add(role='roles/iam.serviceAccountTokenCreator', members=[ executives ])
    iam.bindings.add(role='roles/iam.workloadIdentityUser', members=[ principal ])

    return iam

def workspace_tag(account):
    builder_email = f'serviceAccount:{account.email}'

    iam = Policy()
    iam.bindings.add(role='roles/resourcemanager.tagAdmin', members=[ builder_email ])

    return iam

def workspace_folder(setup, account):
    org = setup['googleOrganization']['name']
    builder_role = f'{org}/roles/{setup["builderRole"]["name"]}'
    builder_email = f'serviceAccount:{account.email}'
    executives = f'group:{setup["googleGroups"]["executive"]}'

    iam = Policy()
    iam.bindings.add(role='roles/resourcemanager.folderAdmin', members=[ executives ])
    iam.bindings.add(role=builder_role, members=[ builder_email ])

    return iam
