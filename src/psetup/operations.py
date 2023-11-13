from time import sleep

# error message if creation status times out
status_timeout = 'timeout before resource creation status is available.'
# error message if creation completion times out
completion_timeout = 'timeout before resource creation is done.'
# error message if the operation message is not well formed
message_error = 'the operation response contained neither a name nor a status.'

def watch(api, operation, period=5, timeout=60):
    if ( not 'name' in operation ) and ( not 'done' in operation ):
         raise RuntimeError(message_error)
    operation_request = api.operations().get(name=operation['name'])

    # this loop will check for updates every 5 seconds during 1 minute.
    time_elapsed = 0
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

    return operation['done']