# Prerequisites

the Google SDK is necessary for the scripts to authenticate to
the Google API. You can rely on Google Cloud Shell for simplicity.

A setup file *setup.yaml*, containing all the specific data from
the organization should be created at the root of this project and fill with
the following schema:

```yaml
# google part
google:
    organization: string, the organization number
    billing_account: string, the ID of an available billing account
    ext_admin_user: string, the email of a backup account
    groups:
        finops_group: string, the email of the group of FinOps
        admins_group: string, the email of the group of Admins
        policy_group: string, the email of the group of Policy admins
        executive_group: string, the email of the group of Executives
# terraform part
terraform:
    organization: string, the name of the Terraform Cloud organization
    workspace_project: string, the ID of the terraform project for workspaces
```
