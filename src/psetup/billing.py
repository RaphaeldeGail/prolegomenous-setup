"""Generate a billing account idempotently.

Can apply a specific configuration for a billing account and create or update
it in order to match the configuration.

Typical usage example:

  generate_account(setup, builder_email)
"""

from google.iam.v1 import iam_policy_pb2
from google.cloud import billing_v1

def _control_access(billing_account, policy):
    """
    Apply IAM policy to the billing account.

    Args:
        billing_account: google.cloud.billing_v1.types.BillingAccount, the
            delcared billing account.
        policy: dict, list all `bindings` to apply to the billing account
            policy.
    """
    client = billing_v1.CloudBillingClient()
    request = iam_policy_pb2.SetIamPolicyRequest(
        resource=billing_account.name,
        policy=policy
    )

    client.set_iam_policy(request=request)

    print('IAM policy set... ', end='')

    return None

def generate_account(setup, builder_email):
    """
    Generate the billing account and related resources. The billing account is
        updated with a new IAM policy.

    Args:
        setup: dict, the configuration used to build the root structure.
    """
    # Sets the variables for generating the billing account

    mail = f'serviceAccount:{builder_email}'
    bill = f'billingAccounts/{setup["google"]["billing_account"]}'
    policy = {
        'bindings': [
            {'members': [mail], 'role': 'roles/billing.user'},
            {'members': [mail], 'role': 'roles/billing.costsManager'},
            {'members': [mail], 'role': 'roles/iam.securityAdmin'}
        ]
    }

    billing_account = billing_v1.BillingAccount(
        name=bill
    )

    _control_access(billing_account, policy)

    return None
