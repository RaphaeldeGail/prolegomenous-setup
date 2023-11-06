def main():
    import time
    from google.auth import default
    from psetup import config, root_project, tags

    ## the scopes for all google API calls
    scopes = ['https://www.googleapis.com/auth/cloud-platform']

    # WARNING: the quota_project_id can not be set when calling the credentials
    # default() method and has to be explicitly overidden with
    # the with_quota_project(None) method.
    credentials = default(scopes=scopes)[0].with_quota_project(None)

    setup = config.from_yaml()
    #print(setup)
    timestamp = time.strftime("%Y-%m-%dT%H-%M", time.localtime())
    print(timestamp)

    print('generating project... ', end='')
    project = root_project.generate_project(credentials=credentials, parent=setup['parent'], executive_group=setup['executive_group'])
    print('generating tag... ', end='')
    tag = tags.generate_root_tag(credentials=credentials, parent=setup['parent'])
    if not tag.is_bound(credentials=credentials, project=project.name):
        print('binding')
        bound = tag.bind(credentials=credentials, project=project.name)
    print('already bound')