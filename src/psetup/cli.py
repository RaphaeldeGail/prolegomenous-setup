def main():
    import time
    from google.auth import default
    from psetup import config, root_project

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

    project = root_project.check_project(credentials=credentials, parent=setup['parent'], executive_group='yo')

    print(project)