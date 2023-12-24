"""Main module for the psetup client.

This module will orchestrate between all resources creation on Google Cloud and
display the command to run for the psetup-billing client subsequently. This
module does not instantiate the resources to create but instead garantees
proper links between them, as imposed by the root structure.
"""

from time import strftime, localtime
from .project import (
    apply_project,
    enable_services,
    control_access as project_access,
    update_billing
)
from .tag import (
    apply_key,
    apply_value,
    apply_binding,
    control_access as tag_access
)
from .workload import (
    apply_pool,
    apply_provider
)
from .service_account import (
    apply_service_account,
    control_access as service_account_access
)
from .folder import (
    apply_folder,
    control_access as folder_access
)
from . import core
from .utils import timestamp

def main():
    """Main entry for the psetup client.
    """
    t0 = localtime()
    print(f'*** Started on {strftime("%Y-%m-%dT%H-%M", t0)} ***')

    ##### Root Project #####

    print('generating root project... ', end='')
    root_project = apply_project(core.root_project)

    enable_services(root_project, core.root_project_services)
    print('services enabled... ', end='')

    project_access(root_project, core.root_project_iam)
    print('IAM policy set... ', end='')

    update_billing(root_project, core.root_project_billing_info)
    print('billing enabled... ', end='')

    print('DONE', end='')

    timestamp(t0)

    ##### Root Tag #####

    fqn = f'//cloudresourcemanager.googleapis.com/{root_project.name}'
    core.root_tag_binding.parent = fqn

    print('generating root tag... ', end='')
    root_tag_key = apply_key(core.root_tag_key)

    core.root_tag_value.parent = root_tag_key.name
    root_tag_value = apply_value(core.root_tag_value)

    core.root_tag_binding.tag_value = root_tag_value.name
    apply_binding(core.root_tag_binding)

    print('DONE', end='')

    timestamp(t0)

    ##### Workload Identity Pool #####

    core.organization_pool.project = root_project.name

    print('generating workload identity pool... ', end='')
    organization_pool = apply_pool(core.organization_pool)

    core.terraform_provider.parent = organization_pool.name
    apply_provider(core.terraform_provider)

    print('DONE', end='')

    timestamp(t0)

    ##### Builder Service Account #####

    pool = f'principalSet://iam.googleapis.com/{organization_pool.name}'
    principal = f'{pool}/attribute.terraform_project_id/{core.wrk_id}'

    core.builder_account.project = root_project.project_id
    core.builder_account_iam.add({
        'role': 'roles/iam.workloadIdentityUser',
        'members': [ principal ]
    })

    print('generating service account... ', end='')
    builder_account = apply_service_account(core.builder_account)

    service_account_access(builder_account, core.builder_account_iam)
    print('IAM policy set... ', end='')

    print('DONE', end='')

    timestamp(t0)

    ##### Workspace Tag #####

    builder_email = f'serviceAccount:{builder_account.email}'
    core.workspace_tag_key_iam.add({
        'role': 'roles/resourcemanager.tagAdmin',
        'members': [ builder_email ]
    })

    print('generating workspace tag... ', end='')
    workspace_tag_key = apply_key(core.workspace_tag_key)

    tag_access(workspace_tag_key, core.workspace_tag_key_iam)
    print('IAM policy set... ', end='')

    print('DONE', end='')

    timestamp(t0)

    ##### Workspace Folder #####

    core.workspace_folder_iam.add({
        'role': core.builder_role,
        'members': [ builder_email ]
    })

    print('generating workspace folder... ', end='')
    workspace_folder = apply_folder(core.workspace_folder)

    folder_access(workspace_folder, core.workspace_folder_iam)
    print('IAM policy set... ', end='')

    print('DONE', end='')

    timestamp(t0)

    ##### #####

    print('***')
    print('You can now run the following command:')
    print(f'BUILDER_EMAIL="{builder_account.email}" psetup-billing')
