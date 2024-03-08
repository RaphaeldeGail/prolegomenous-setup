"""Manage a billing account idempotently.

The billing account IAM policy can be updated with this module.

Typical usage example:

  billing.control(my_billing_account, {billingAccountPolicy})
"""

from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest
from google.cloud.billing_v1 import CloudBillingClient

def control(billing_account, policy):
    """Apply IAM policy to the billing account.

    Args:
        billing_account: string, the fully qualified name for the billing
            account.
        policy: google.iam.v1.policy_pb2.Policy, the policy to apply.
    """
    client = CloudBillingClient()
    request = SetIamPolicyRequest(
        resource=billing_account,
        policy=policy
    )

    client.set_iam_policy(request=request)

    return None
