"""Main module for the psetup client.

This module will orchestrate between all resources creation on Google Cloud and
display the command to run for the psetup-billing client subsequently.
"""

def main():
    """
    Main entry for the psetup client.

    """
    from time import strftime, localtime
    from psetup import config, project, tag, workload, service_account, folder

    setup = config.from_yaml()
    timestamp = strftime('%Y-%m-%dT%H-%M', localtime())
    print(timestamp)

    print('generating root project... ', end='')
    root_project = project.generate_root(setup=setup)
    project_name = root_project.name
    print('DONE')

    print('generating root tag... ', end='')
    tag.generate_root_tag(setup=setup, project=project_name)
    print('DONE')

    print('generating workload identity pool... ', end='')
    org_pool = workload.generate_terraform_provider(
        setup=setup,
        project=project_name
    )
    print('DONE')

    print('generating service account... ', end='')
    builder_account = service_account.generate_service_account(
        setup=setup,
        parent=root_project.project_id,
        pool_id=org_pool.name
    )
    builder_email = builder_account.name.split('/serviceAccounts/')[1]
    print('DONE')

    print('generating workspace tag... ', end='')
    tag.generate_workspace_tag(
        setup=setup,
        builder_email=builder_email
    )
    print('DONE')

    print('generating workspace folder... ', end='')
    folder.generate_folder(
        setup=setup,
        builder_email=builder_email
    )
    print('DONE')

    print('Run the command:')
    print(f'export BUILDER_EMAIL="{builder_email}"; psetup-billing')
