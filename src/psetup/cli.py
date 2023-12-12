def main():
    """
    Main entry for the psetup client.

    """
    from time import strftime, localtime
    from psetup import config, project, tag, workload, service_account, folder

    setup = config.from_yaml()
    timestamp = strftime("%Y-%m-%dT%H-%M", localtime())
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
        poolId=org_pool.name
    )
    builder_email = builder_account.name.split('/serviceAccounts/')[1]
    print('DONE')
    
    print('generating workspace tag... ', end='')
    workspace_tag = tag.generate_workspace_tag(
        setup=setup,
        builder_email=builder_email
    )
    print('DONE')

    print('generating workspace folder... ', end='')
    workspace_folder = folder.generate_folder(
        setup=setup,
        builder_email=builder_email
    )
    print('DONE')

    print('Run the command:')
    print('export BUILDER_EMAIL="{0}"; psetup-billing'.format(builder_email))