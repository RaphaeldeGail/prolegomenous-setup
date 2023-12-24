from .config import from_yaml
from .operation import IamPolicy
from google.cloud.resourcemanager_v3 import (
    Project,
    TagKey,
    TagValue,
    TagBinding,
    Folder
)
from google.cloud.billing_v1 import ProjectBillingInfo
from random import randint
from .workload import WorkloadIdentityPool, WorkloadIdentityProvider
from .service_account import ServiceAccount

setup = from_yaml()

exec_grp = f'group:{setup["google"]["groups"]["executive_group"]}'
billing_account = f'billingAccounts/{setup["google"]["billing_account"]}'
uuid = str(randint(1,999999))

pool_id = setup['organizationPool']['id']
org_name = setup['google']['org_name']
terraform_org = setup['terraform']['organization']
condition = f'organization:{terraform_org}:project:Workspaces'
attribute_condition = f'assertion.sub.startsWith("{condition}")'
oidc = {
    'allowedAudiences': [f'https://tfc.{org_name}'],
    'issuerUri': setup['terraformProvider']['oidc']['issuerUri']
}

wrk_id = setup['terraform']['workspace_project']

role  = setup["workspaceFolder"]["builderRole"]
builder_role = f'{setup["parent"]}/roles/{role}'

root_project = Project(
    parent=setup['parent'],
    project_id=f'{setup["rootProject"]["displayName"]}-{uuid}',
    display_name=setup['rootProject']['displayName'],
    labels=setup['rootProject']['labels']
)
root_project_services = setup['rootProject']['services']
root_project_iam = IamPolicy([{
    'role': 'roles/owner',
    'members': [ exec_grp ]
}])
root_project_billing_info = ProjectBillingInfo(
    billing_account_name=billing_account
)

root_tag_key = TagKey(
    parent=setup['parent'],
    short_name=setup['rootTag']['shortName'],
    description=setup['rootTag']['description'],
)
root_tag_value = TagValue(
    short_name=setup['trueValue']['shortName'],
    description=setup['trueValue']['description'],
)
root_tag_binding = TagBinding()

organization_pool = WorkloadIdentityPool(
    pool_id=pool_id,
    description=setup['organizationPool']['description'],
    display_name=pool_id.replace('-', ' ').title()
)
terraform_provider = WorkloadIdentityProvider(
    provider_id=setup['terraformProvider']['id'],
    description=setup['terraformProvider']['description'],
    display_name=setup['terraformProvider']['displayName'],
    oidc= oidc,
    attribute_mapping=setup['terraformProvider']['attributeMapping'],
    attribute_condition=attribute_condition
)

builder_account = ServiceAccount(
    account_id=setup['builderAccount']['name'],
    display_name=setup['builderAccount']['displayName'],
    description=setup['builderAccount']['description']
)
builder_account_iam = IamPolicy([{
    'role': 'roles/iam.serviceAccountTokenCreator',
        'members': [ exec_grp ]
}])

workspace_tag_key = TagKey(
    parent=setup['parent'],
    short_name=setup['workspaceTag']['shortName'],
    description=setup['workspaceTag']['description'],
)
workspace_tag_key_iam = IamPolicy()

workspace_folder = Folder(
    parent=setup['parent'],
    display_name=setup['workspaceFolder']['displayName']
)
workspace_folder_iam = IamPolicy([{
    'role': 'roles/resourcemanager.folderAdmin',
    'members': [ exec_grp ]
}])