# Prerequisites

## Google Accounts

In order to create the necessary building blocks for the root strucure you will
need several accounts with high-level permission:

* an *Executive* account with permissions to create projects and folders
* a *Finops* account with permissions to set IAM policy to billing accounts

Usage of a single account with all permissions is discouraged.

## Authentication Process

the Google SDK is necessary for the scripts to authenticate to
the Google API. You can rely on Google Cloud Shell for simplicity.

Before calling a client, make sure to have the environment variable
**GOOGLE_APPLICATION_CREDENTIALS** pointing to the right Google account. Only
access to Google Cloud APIs are necessary so it is encouraged to rely on
*Application Default Credentials*, with the following command:

```bash
gcloud auth application-default login
```

## The *Environment* File

A specific configuration file *environment.yaml*, containing all the specific
data from the organization should be created at the root of this project and
fill with the following schema:

```yaml
# google part
googleCloudOrganization:
    name: string, the organization number
    billingAccount: string, the ID of an available billing account
    extAdminUser: string, the email of a backup account
    groups:
        finopsGroup: string, the email of the group of FinOps
        adminsGroup: string, the email of the group of Admins
        policyGroup: string, the email of the group of Policy admins
        executiveGroup: string, the email of the group of Executives
# terraform part
terraformCloudOrganization:
    name: string, the name of the Terraform Cloud organization
    workspaceProject: string, the ID of the terraform project for workspaces
```
