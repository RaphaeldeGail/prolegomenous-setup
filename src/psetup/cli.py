"""Main module for the psetup client.

This module will orchestrate between all resources creation on Google Cloud and
display the command to run for the psetup-billing client subsequently.
"""

from time import strftime, localtime
from random import randint
from psetup import config, project, tag, workload
from google.cloud import resourcemanager_v3
from google.cloud import billing_v1

def main():
    """Main entry for the psetup client.

    """
    timestamp = strftime('%Y-%m-%dT%H-%M', localtime())
    print(f'*** Started on {timestamp} ***')
    setup = config.from_yaml()

    exec_grp = f'group:{setup["google"]["groups"]["executive_group"]}'
    billing_account = f'billingAccounts/{setup["google"]["billing_account"]}'
    uuid = str(randint(1,999999))

    root_project = resourcemanager_v3.Project(
        parent=setup['parent'],
        project_id=f'{setup["rootProject"]["displayName"]}-{uuid}',
        display_name=setup['rootProject']['displayName'],
        labels=setup['rootProject']['labels']
    )
    root_project_services = setup['rootProject']['services']
    root_project_iam = {
        'bindings': [{'members': [exec_grp], 'role': 'roles/owner'}]
    }
    root_project_billing_info = billing_v1.ProjectBillingInfo(
        billing_account_name=billing_account
    )

    root_tag_key = resourcemanager_v3.TagKey(
        parent=setup['parent'],
        short_name=setup['rootTag']['shortName'],
        description=setup['rootTag']['description'],
    )
    root_tag_value = resourcemanager_v3.TagValue(
        short_name=setup['trueValue']['shortName'],
        description=setup['trueValue']['description'],
    )

    ##### Root Project #####

    print('generating root project... ', end='')
    root_project = project.apply_project(root_project)

    project.enable_services(root_project, root_project_services)
    print('services enabled... ', end='')

    project.control_access(root_project, root_project_iam)
    print('IAM policy set... ', end='')

    project.update_billing(root_project, root_project_billing_info)
    print('billing enabled... ', end='')

    print('DONE')

    fqn = f'//cloudresourcemanager.googleapis.com/{root_project.name}'
    root_tag_binding = resourcemanager_v3.TagBinding(
        parent=fqn
    )

    ##### Root Tag #####

    print('generating root tag... ', end='')
    root_tag_key = tag.apply_key(root_tag_key)

    root_tag_value.parent = root_tag_key.name
    root_tag_value = tag.apply_value(root_tag_value)

    root_tag_binding.tag_value = root_tag_value.name
    root_tag_binding = tag.apply_binding(root_tag_binding)

    print('DONE')

    pool_id = setup['organizationPool']['id']
    org_name = setup['google']['org_name']
    terraform_org = setup['terraform']['organization']
    condition = f'organization:{terraform_org}:project:Workspaces'
    attribute_condition = f'assertion.sub.startsWith("{condition}")'
    oidc = {
        'allowedAudiences': [f'https://tfc.{org_name}'],
        'issuerUri': setup['terraformProvider']['oidc']['issuerUri']
    }

    organization_pool = workload.WorkloadIdentityPool(
        pool_id=pool_id,
        project=root_project.name,
        description=setup['organizationPool']['description'],
        display_name=pool_id.replace('-', ' ').title()
    )
    terraform_provider = workload.WorkloadIdentityProvider(
        provider_id=setup['terraformProvider']['id'],
        description=setup['terraformProvider']['description'],
        display_name=setup['terraformProvider']['displayName'],
        oidc= oidc,
        attribute_mapping=setup['terraformProvider']['attributeMapping'],
        attribute_condition=attribute_condition
    )

    ##### Workload Identity Pool #####

    print('generating workload identity pool... ', end='')
    organization_pool = workload.apply_pool(organization_pool)

    terraform_provider.parent = organization_pool.name
    terraform_provider = workload.apply_provider(terraform_provider)

    print('DONE')

    # print('generating service account... ', end='')
    # builder_account = service_account.generate_service_account(
    #     setup=setup,
    #     parent=root_project.project_id,
    #     pool_id=org_pool.name
    # )
    # builder_email = builder_account.name.split('/serviceAccounts/')[1]
    # print('DONE')

    # print('generating workspace tag... ', end='')
    # tag.generate_workspace_tag(
    #     setup=setup,
    #     builder_email=builder_email
    # )
    # print('DONE')

    # print('generating workspace folder... ', end='')
    # folder.generate_folder(
    #     setup=setup,
    #     builder_email=builder_email
    # )
    # print('DONE')

    # print('***')
    # print('You can now run the following command:')
    # print(f'BUILDER_EMAIL="{builder_email}" psetup-billing')
