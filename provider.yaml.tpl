attributeCondition: assertion.sub.startsWith("organization:%TFC_ORGANIZATION%:project:Workspaces")
attributeMapping:
  attribute.aud: assertion.aud
  attribute.terraform_full_workspace: assertion.terraform_full_workspace
  attribute.terraform_organization_id: assertion.terraform_organization_id
  attribute.terraform_organization_name: assertion.terraform_organization_name
  attribute.terraform_project_id: assertion.terraform_project_id
  attribute.terraform_project_name: assertion.terraform_project_name
  attribute.terraform_run_id: assertion.terraform_run_id
  attribute.terraform_run_phase: assertion.terraform_run_phase
  attribute.terraform_workspace_id: assertion.terraform_workspace_id
  attribute.terraform_workspace_name: assertion.terraform_workspace_name
  google.subject: assertion.sub
description: Terraform Cloud identity provider.
displayName: Terraform Cloud OIDC Provider
name: projects/%PROJECT_NUMBER%/locations/global/workloadIdentityPools/organization-identity-pool/providers/tfc-oidc
oidc:
  allowedAudiences:
  - https://tfc.%ORGANIZATION_DOMAIN%
  issuerUri: https://app.terraform.io
state: ACTIVE