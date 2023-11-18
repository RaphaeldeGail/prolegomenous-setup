def main():
    import time
    from google.auth import default
    from psetup import config, project, tag, workload, service_account, folder

    ## the scopes for all google API calls
    scopes = ['https://www.googleapis.com/auth/cloud-platform']

    # WARNING: the quota_project_id can not be set when calling the credentials
    # default() method and has to be explicitly overidden with
    # the with_quota_project(None) method.
    credentials = default(scopes=scopes)[0].with_quota_project(None)

    setup = config.from_yaml(credentials=credentials)
    timestamp = time.strftime("%Y-%m-%dT%H-%M", time.localtime())
    print(timestamp)

    print('generating root project... ', end='')
    root_project = project.generate_project(credentials=credentials, setup=setup)
    project_name = root_project.name
    print('generating root tag... ', end='')
    root_tag = tag.generate_root_tag(credentials=credentials, setup=setup)
    if not root_tag.is_bound(credentials=credentials, project=project_name):
        print('binding root tag... ', end='')
        bound = root_tag.bind(credentials=credentials, project=project_name)
    print('generating workload identity pool... ', end='')
    pool = workload.generate_provider(credentials=credentials, setup=setup, parent=project_name)
    print('generating service account... ', end='')
    builder_account = service_account.generate_service_account(credentials=credentials, setup=setup, parent=root_project.data['projectId'], poolId=pool.name)
    builder_email = builder_account.name.split('/serviceAccounts/')[1]
    print('generating workspace tag... ', end='')
    workspace_tag = tag.generate_workspace_tag(credentials=credentials, setup=setup, builder_email=builder_email)
    print('generating workspace folder... ', end='')
    workspace_folder = folder.generate_folder(credentials=credentials, setup=setup, builder_email=builder_email)