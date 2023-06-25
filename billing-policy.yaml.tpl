bindings:
- members:
  - serviceAccount:%BUILDER_EMAIL%
  role: roles/billing.user
- members:
  - serviceAccount:%BUILDER_EMAIL%
  role: roles/billing.costsManager
- members:
  - serviceAccount:%BUILDER_EMAIL%
  role: roles/iam.securityAdmin
etag: %ETAG%
version: 1