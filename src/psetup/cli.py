def main():
    import time
    from google.auth import default
    from psetup import config, root_project, tags, workload, service_account, folder

    ## the scopes for all google API calls
    scopes = ['https://www.googleapis.com/auth/cloud-platform']

    # WARNING: the quota_project_id can not be set when calling the credentials
    # default() method and has to be explicitly overidden with
    # the with_quota_project(None) method.
    credentials = default(scopes=scopes)[0].with_quota_project(None)

    setup = config.from_yaml(credentials=credentials)
    #print(setup)
    timestamp = time.strftime("%Y-%m-%dT%H-%M", time.localtime())
    print(timestamp)

    print('generating root project... ', end='')
    project = root_project.generate_project(credentials=credentials, parent=setup['parent'], executive_group=setup['google']['groups']['executive_group'])
    print('generating root tag... ', end='')
    tag = tags.generate_root_tag(credentials=credentials, parent=setup['parent'])
    if not tag.is_bound(credentials=credentials, project=project.name):
        print('binding root tag... ', end='')
        bound = tag.bind(credentials=credentials, project=project.name)
    print('generating workload identity pool... ', end='')
    pool = workload.generate_provider(credentials=credentials, parent=project.name, terraform_org=setup['terraform']['organization'], org_name=setup['google']['org_name'])
    print('generating service account... ', end='')
    service_account = service_account.generate_service_account(credentials=credentials, parent=project.data['projectId'], poolId=pool.name, wrkId=setup['terraform']['workspace_project'], executive_group=setup['google']['groups']['executive_group'])
    print('generating workspace tag... ', end='')
    tag = tags.generate_workspace_tag(credentials=credentials, parent=setup['parent'], builder_email=service_account.name.split('/serviceAccounts/')[1])
    print('generating workspace folder... ', end='')
    folder = folder.generate_folder(credentials=credentials, parent=setup['parent'], executive_group=setup['google']['groups']['executive_group'], builder_email=service_account.name.split('/serviceAccounts/')[1])