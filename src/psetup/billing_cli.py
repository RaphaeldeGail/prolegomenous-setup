def main():
    """
    Main entry for the psetup-billing client.

    """
    from time import strftime, localtime
    from psetup import config, billing
    from os import getenv

    setup = config.from_yaml()
    timestamp = strftime("%Y-%m-%dT%H-%M", localtime())
    print(timestamp)

    builder_email = getenv('BUILDER_EMAIL')
    
    if builder_email is None:
        raise ValueError('BUILDER_EMAIL environment variable empty')

    print('generating billing account... ', end='')
    billing.generate_account(setup, builder_email)
    print('DONE')