"""Manipulate long-running operations for Google Cloud resources.

Can wait for an operation to complete before returning the result of the
completed operation.

Typical usage example:

  result = operation.watch(api=api, operation=operation)
"""

from time import sleep, localtime, mktime

class IamPolicy():
    """A class to represent a service account in Google Cloud project.

    Attributes:
        account_id: string, the ID for the service account, which becomes the
            final component of the resource name.
        description: string, a description of the service account.
        display_name: string, a user-friendly name for the service account.
        project: string, the ID of the project to create this account in.

    """

    def __init__(self, bindings=None):
        # Initial empty `bindings` list
        self.bindings = {}

        if bindings:
            for binding in bindings:
                if not binding['role'] in self.bindings:
                    self.bindings.update({binding['role']: binding['members']})
                else:
                    self.bindings[binding['role']].extend(binding['members'])

    @property
    def policy(self):
        fmt = {
            'bindings': [
                {
                    'role': role,
                    'members': members
                } for role, members in self.bindings.items()
            ]
        }
        return fmt

    def add(self, binding):
        if not binding['role'] in self.bindings:
            self.bindings.update({binding['role']: binding['members']})
        else:
            self.bindings[binding['role']].extend(binding['members'])

def timestamp(t0):
    tf = localtime()
    print(f' ({mktime(tf) - mktime(t0)} seconds)')

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
        raise RuntimeError(f'operation ended in error: {str(operation)}')

    if not 'response' in operation:
        return {}

    return operation['response']
