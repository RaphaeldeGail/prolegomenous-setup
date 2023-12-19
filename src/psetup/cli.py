"""Main module for the psetup client.

This module will orchestrate between all resources creation on Google Cloud and
display the command to run for the psetup-billing client subsequently.
"""

from time import strftime, localtime
from random import randint
from psetup import config, project
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

    ##### Root Tag #####

    # print('generating root tag... ', end='')
    # tag.generate_root_tag(setup=setup, project=project_name)
    # print('DONE')

    # print('generating workload identity pool... ', end='')
    # org_pool = workload.generate_terraform_provider(
    #     setup=setup,
    #     project=project_name
    # )
    # print('DONE')

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
