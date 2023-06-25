bindings:
- members:
  - group:%EXECUTIVE_GROUP%
  role: roles/resourcemanager.folderAdmin
- members:
  - serviceAccount:%BUILDER_EMAIL%
  role: organizations/%ORGANIZATION_ID%/roles/workspaceBuilder
etag: %ETAG%
version: 1