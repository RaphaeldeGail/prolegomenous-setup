from time import sleep

def watch(api, name, period=5, timeout=60):
    # error message if creation status times out
    status_timeout = 'timeout before resource creation status is available.'
    # error message if creation completion times out
    completion_timeout = 'timeout before resource creation is done.'
    operation_request = api.operations().get(name=name)

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    operation = operation_request.execute()
    while not 'done' in operation:
        if time_elapsed > timeout % period :
            raise RuntimeError(status_timeout)
        time_elapsed += 1
        sleep(period)
        operation = operation_request.execute()

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
    while operation['done'] is False:
        if time_elapsed > timeout % period :
            raise RuntimeError(completion_timeout)
        time_elapsed += 1
        sleep(period)
        operation = operation_request.execute()

    return operation['response']