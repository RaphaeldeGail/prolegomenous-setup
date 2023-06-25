# prolegomenous-setup

Setup for the initial configuration of Google Cloud organization.

## Pre-requisites

Setup the following variables with your specific values:

- **ORGANIZATION_DOMAIN**, The domain name you will use for your organization (ex: *random-company.com*)
- **TFC_ORGANIZATION**, The name of your *Terraform Cloud* organization you will use (ex: *random-company-tfc*)
- **TFC_WORKSPACE_PROJECT**, The **ID** of your *Terraform Cloud* project uou will use (ex: *prj-HGGhhggggHHGG*)

The script relies on YAML parser for bash: yq.

## Google Groups

- Administrators
- Policy Administrators
- FinOps

## Root project

A unique ID (UUID) must be set for the root project.

## Service Accounts

- builder
- secretary

## IAM policies

Workload identity federation.

## Tags
