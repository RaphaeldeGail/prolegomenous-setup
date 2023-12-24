"""Main module for the psetup-billing client.

This module will orchestrate between all financial resources creation on Google
Cloud .
"""

from time import strftime, localtime
from os import getenv
from google.cloud.billing_v1 import BillingAccount
from .config import from_yaml
from .billing import control_access
from .utils import IamPolicy, timestamp

def main():
    """
    Main entry for the psetup-billing client.

    """
    t0 = localtime()
    print(f'*** Started on {strftime("%Y-%m-%dT%H-%M", t0)} ***')

    builder_email = getenv('BUILDER_EMAIL')

    if builder_email is None:
        raise ValueError('BUILDER_EMAIL environment variable empty')

    setup = from_yaml()
    mail = f'serviceAccount:{builder_email}'
    billing_account = f'billingAccounts/{setup["google"]["billing_account"]}'
    billing_account_iam = IamPolicy([
        {'members': [ mail ], 'role': 'roles/billing.user'},
        {'members': [ mail ], 'role': 'roles/billing.costsManager'},
        {'members': [ mail ], 'role': 'roles/iam.securityAdmin'}
    ])

    billing_account = BillingAccount(
        name=billing_account
    )

    ##### Billing Account #####

    print('generating billing account... ', end='')
    control_access(billing_account, billing_account_iam)

    print('DONE', end='')

    timestamp(t0)
