"""Main module for the psetup-billing client.

This module will orchestrate between all financial resources creation on Google
Cloud .
"""

from time import strftime, localtime
from os import getenv
from .config import from_yaml
from .billing import generate_account


def main():
    """
    Main entry for the psetup-billing client.

    """
    setup = from_yaml()
    timestamp = strftime('%Y-%m-%dT%H-%M', localtime())
    print(timestamp)

    builder_email = getenv('BUILDER_EMAIL')

    if builder_email is None:
        raise ValueError('BUILDER_EMAIL environment variable empty')

    print('generating billing account... ', end='')
    generate_account(setup, builder_email)
    print('DONE')
