bindings:
- members:
  - group:%EXECUTIVE_GROUP%
  role: roles/iam.serviceAccountTokenCreator
- members:
  - principalSet://iam.googleapis.com/projects/%PROJECT_NUMBER%/locations/global/workloadIdentityPools/%WRK_ID_POOL%/attribute.terraform_project_id/%TFC_WORKSPACE_PROJECT%
  role: roles/iam.workloadIdentityUser
etag: %ETAG%
version: 1