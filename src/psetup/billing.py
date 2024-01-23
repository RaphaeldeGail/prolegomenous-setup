"""Generate a billing account idempotently.

Can apply a specific configuration for a billing account and create or update
it in order to match the configuration.

Typical usage example:

  generate_account(setup, builder_email)
"""

from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest
from google.cloud.billing_v1 import CloudBillingClient

def control_access(billing_account, policy):
    """
    Apply IAM policy to the billing account.

    Args:
        billing_account: google.cloud.billing_v1.types.BillingAccount, the
            delcared billing account.
        policy: dict, list all `bindings` to apply to the billing account
            policy.
    """
    client = CloudBillingClient()
    request = SetIamPolicyRequest(
        resource=billing_account.name,
        policy=policy.format
    )

    client.set_iam_policy(request=request)

    print('IAM policy set... ', end='')

    return None
