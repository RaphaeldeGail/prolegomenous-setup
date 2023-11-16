from time import sleep

# error message if creation status times out
status_timeout = 'timeout before resource creation status is available.'
# error message if creation completion times out
completion_timeout = 'timeout before resource creation is done.'
# error message if the operation message is not well formed
message_error = 'the operation response contained neither a name nor a status.'

def watch(api, operation, period=5, timeout=60):
    """
    Wait for an operation to complete before returning the complettion message.
        A completed operation should contain the item "done: True" in its
        message.

    Args:
        api: api, the base Google api with the operations resource.
        operation: operation, the initial operation response delivered by some
            request.
        period: int, the time interval, in seconds, between two consecutive
            checks of the operation status. Defaults to 5.
        timeout: int, the maximum time interval to wait before the operation
            is considered a failure if it is not already completed.

    Returns:
        operation, the final operation response after it reached completion.

    Raises:
        RuntimeError, Raises an exception if the initial operation does not
            bear a name nor a status.
        RuntimeError, Raises an exception if the operation times out before an
            operation status could be received.
        RuntimeError, Raises an exception if the operation times out before its
            status reaches completion.
        RuntimeError, Raises an exception if the final response contains an
            error entry.
        RuntimeError, Raises an exception if the final operation message does
            not contain a response entry.
    """
    if ( not 'name' in operation ) and ( not 'done' in operation ):
         raise RuntimeError(message_error)
    
    if ( not 'name' in operation ) and ( operation['done'] ):
        return operation
        
    request = api.operations().get(name=operation['name'])
    # this loop will check for updates every (period=5) seconds during
    # (timeout=60) seconds.
    time_elapsed = 0
    while not 'done' in operation:
        if time_elapsed > timeout % period :
            raise RuntimeError(status_timeout)
        time_elapsed += 1
        sleep(period)
        operation = request.execute()

    # this loop will check for updates every (period=5) seconds during
    # (timeout=60) seconds.
    time_elapsed = 0
    while operation['done'] is False:
        if time_elapsed > timeout % period :
            raise RuntimeError(completion_timeout)
        time_elapsed += 1
        sleep(period)
        operation = request.execute()

    # after the operation 'done' is True, there should be either a response or
    # error entry.
    if 'error' in operation:
        raise RuntimeError('operation ended in error: {0}'.format(str(operation)))

    if not 'response' in operation:
        raise RuntimeError('no response found: {0}'.format(str(operation)))

    return operation