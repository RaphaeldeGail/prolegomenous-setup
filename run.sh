#!/bin/bash

# Initializes root project and Workspaces folder along with workload identity federation and service account.
# Script should be executed by an Organization Executive for correct permissions

# TODO: use custom roles for billing and tags policy
# TODO: add a budget

# Uncomment line below to track command line invocations
#set -x

echo -e "   -----\n   Start of script\n   -----"

# Check for pre-requisite variables
# ORGANIZATION_DOMAIN, TFC_ORGANIZATION and TFC_WORKSPACE_PROJECT
if [ -z "$ORGANIZATION_DOMAIN" ]; then
  echo 'Please set the ORGANIZATION_DOMAIN variable before executing this script.'
  exit 1
fi
if [ -z "$TFC_ORGANIZATION" ]; then
  echo 'Please set the TFC_ORGANIZATION variable before executing this script.'
  exit 1
fi
if [ -z "$TFC_WORKSPACE_PROJECT" ]; then
  echo 'Please set the TFC_WORKSPACE_PROJECT variable before executing this script.'
  exit 1
fi

# Compute organization ID
ORGANIZATION_ID=$(gcloud organizations describe $ORGANIZATION_DOMAIN --format="value(name)" | cut -d'/' -f 2)

# Random unique user ID for the root project
UUID=$RANDOM
# Default name for the workload identity pool
WRK_ID_POOL="organization-identity-pool"

# * Create the google groups in Cloud identity
EXECUTIVE_GROUP="org-executives@$ORGANIZATION_DOMAIN"

# Define functions
get_yq() {
  YQ_VERSION=$(yq -V 2>&1)
  if [ $? -ne 0 ]; then
    echo -n 'yq utility will be installed... '
    CURL_RESULT=$(sudo curl -sL -o /usr/local/bin/yq 'https://github.com/mikefarah/yq/releases/download/v4.32.2/yq_linux_amd64' && sudo chmod +x /usr/local/bin/yq)
    if [ $? -ne 0 ]; then
      echo 'Failed to download yq utility.'
      echo $CURL_RESULT
      return 1
    fi
    YQ_VERSION=$(yq -V 2>&1)
    if [ $? -ne 0 ]; then
      echo 'Failed to load yq utility.'
      echo $YQ_VERSION
      return 1
    fi
    echo 'Installation completed.'
  fi
  echo -n 'yq utility is installed with version: '
  echo "$YQ_VERSION" | sed -E 's/^.*(v[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}).*$/\1/'
  return 0
}

get_root_project() {
  # Check for already existing root project
  read -r PROJECT_ID UUID PROJECT_NUMBER <<< $(gcloud projects list --filter="labels.root=true AND parent.type=organization" --format="value(PROJECT_ID,labels.uuid,projectNumber)")

  # Creates project if does not already exist
  if [ -z "$PROJECT_ID" ]; then
    echo -n "The root project wil be created... "
    PROJECT_ID="root-$UUID"
    gcloud projects create $PROJECT_ID --organization="$ORGANIZATION_ID" --labels=root=true,uuid=$UUID --name="root" --no-enable-cloud-apis
    echo 'Creation completed.'
  fi
  echo "Root project exists with UUID: $UUID"
  gcloud config set project $PROJECT_ID --quiet

  # Enable the list of API for the root project
  SERVICES_CURRENT=$(gcloud services list --enabled --format="value(NAME)")
  # This diff only verifies if all services declared in the yaml file are present in the gcloud command, but not the opposite.
  DIFF=$(diff --changed-group-format='%<' --unchanged-group-format='' <(yq e '.[]' services.yaml | sort) <(echo "$SERVICES_CURRENT" | sort))
  if ! [ -z "$DIFF" ]; then
    echo -n "The project services wil be enabled... "
    echo "$DIFF"
    gcloud services enable $(yq e '.[]' services.yaml | tr '\n' ' ') --quiet
    echo 'Enabling completed.'
  fi
  echo "The project services are enabled."

  # Create the IAM binding matrix at the root project
  POLICY_CURRENT=$(gcloud projects get-iam-policy $PROJECT_ID)

  ETAG=$(echo "$POLICY_CURRENT" | yq -P '.etag')
  sed -e "s;%EXECUTIVE_GROUP%;$EXECUTIVE_GROUP;g" \
  -e "s;%ETAG%;$ETAG;g" project-policy.yaml.tpl > project-policy.yaml

  DIFF=$(diff <(yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)' project-policy.yaml) <(echo "$POLICY_CURRENT" | yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)'))
  if ! [ -z  "$DIFF" ]; then
    echo -n 'Root project policies will be updated... '
    echo "$DIFF"
    gcloud projects set-iam-policy $PROJECT_ID project-policy.yaml --quiet --verbosity=error
    echo 'Update completed.'
  fi
  echo "Root project policies are up to date."
  rm -f project-policy.yaml
}

get_workload_identity_pool() {
  # Create workload identity federation
  WRK_ID_POOL_CURRENT=$(gcloud iam workload-identity-pools describe organization-identity-pool --location="global")
  if [ $? -ne 0 ]; then
    echo -n "The \"Workload Identity Pool\" will be created... " 
    gcloud iam workload-identity-pools create $WRK_ID_POOL --location="global" --display-name="Organization Identity Pool" \
    --description="Workload identity pool for the \"$ORGANIZATION_DOMAIN\" organization."
    echo 'Creation completed.'
  fi
  echo "The Workload Identity Pool \"$WRK_ID_POOL\" exists."
  # Create the OIDC provider for Terraform Cloud
  # Create the map of mapping of attributes from the YAML file
  MAPPING=$(yq '.[] as $item ireduce([]; . + ( [($item | keys)[0], [$item | ..][1]] | join("=") ) ) | join(",")' mapping.yaml)
  PROVIDER_CURRENT=$(gcloud iam workload-identity-pools providers describe tfc-oidc --location="global" --workload-identity-pool=$WRK_ID_POOL)
  if [ $? -ne 0 ]; then
    echo -n "The terraform provider will be created... "
    gcloud iam workload-identity-pools providers create-oidc tfc-oidc --location="global" --workload-identity-pool=$WRK_ID_POOL \
    --attribute-mapping="$MAPPING" --issuer-uri="https://app.terraform.io" --display-name="Terraform Cloud OIDC Provider" \
    --description="Terraform Cloud identity provider." --allowed-audiences="https://tfc.$ORGANIZATION_DOMAIN" \
    --attribute-condition="assertion.sub.startsWith(\"organization:$TFC_ORGANIZATION:project:Workspaces\")"
    echo 'Creation completed.'
  fi

  sed -e "s;%TFC_ORGANIZATION%;$TFC_ORGANIZATION;g" \
  -e "s;%PROJECT_NUMBER%;$PROJECT_NUMBER;g" \
  -e "s;%ORGANIZATION_DOMAIN%;$ORGANIZATION_DOMAIN;g" provider.yaml.tpl > provider.yaml

  DIFF=$(diff <(yq -P 'sort_keys(...) | ... comments=""' provider.yaml) <(echo "$PROVIDER_CURRENT" | yq -P 'sort_keys(...) | ... comments=""'))
  if ! [ -z "$DIFF" ]; then
    echo -n "The terraform provider will updated... "
    echo "$DIFF"
    gcloud iam workload-identity-pools providers update-oidc tfc-oidc --location="global" --workload-identity-pool=$WRK_ID_POOL \
    --attribute-mapping="$MAPPING" --issuer-uri="https://app.terraform.io" --display-name="Terraform Cloud OIDC Provider" \
    --description="Terraform Cloud identity provider." --allowed-audiences="https://tfc.$ORGANIZATION_DOMAIN" \
    --attribute-condition="assertion.sub.startsWith(\"organization:$TFC_ORGANIZATION:project:Workspaces\")"
    echo 'Update completed.'
  fi
  echo "The terraform provider \"tfc-oidc\" exists."
  rm provider.yaml
}

get_builder_account() {
  # Create a builder account in the root project
  BUILDER_EMAIL=$(gcloud iam service-accounts describe builder@$PROJECT_ID.iam.gserviceaccount.com --format="value(email)")
  if [ $? -ne 0 ]; then
    echo -n 'The "builder" service account will be created... '
    BUILDER_EMAIL=$(gcloud iam service-accounts create builder --description="Service account for building workspaces." --display-name="Workspace Builder Service Account" --format="value(email)")
    echo 'Creation completed.'
  fi
  echo "The \"builder\" service account exists with email: $BUILDER_EMAIL"

  # Promote the organization admins group and the Terraform Cloud OIDC provider with ServiceAccount Impersonator of the builder
  POLICY_CURRENT=$(gcloud iam service-accounts get-iam-policy $BUILDER_EMAIL)

  ETAG=$(echo "$POLICY_CURRENT" | yq -P '.etag')
  sed -e "s;%EXECUTIVE_GROUP%;$EXECUTIVE_GROUP;g" \
  -e "s;%PROJECT_NUMBER%;$PROJECT_NUMBER;g" \
  -e "s;%WRK_ID_POOL%;$WRK_ID_POOL;g" \
  -e "s;%TFC_WORKSPACE_PROJECT%;$TFC_WORKSPACE_PROJECT;g" \
  -e "s;%ETAG%;$ETAG;g" builder-account-policy.yaml.tpl > builder-account-policy.yaml

  DIFF=$(diff <(yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)' builder-account-policy.yaml) <(echo "$POLICY_CURRENT" | yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)'))
  if ! [ -z  "$DIFF" ]; then
    echo -n 'The "builder" service account policies will be updated... '
    echo "$DIFF"
    gcloud iam service-accounts set-iam-policy $BUILDER_EMAIL builder-account-policy.yaml --quiet --verbosity=error
    echo 'Update completed.'
  fi
  echo 'The "builder" service account policies are up to date.'
  rm builder-account-policy.yaml
}

get_workspaces_folder() {
  FOLDER_ID=$(gcloud resource-manager folders list --organization="$ORGANIZATION_ID" --filter='DISPLAY_NAME="Workspaces"' --format="value(ID)")

  # Creates project if does not already exist
  if [ -z "$FOLDER_ID" ]; then
    echo -n "The \"Workspaces\" folder will be created... "  
    FOLDER_ID=$(gcloud resource-manager folders create --display-name="Workspaces" --organization="$ORGANIZATION_ID" --format="value(ID)")
    echo 'Creation completed.'
  fi
  echo "The folder \"Workspaces\" exists with FOLDER_ID: $FOLDER_ID"

  # Create the IAM binding matrix for the Workspaces folder
  POLICY_CURRENT=$(gcloud resource-manager folders get-iam-policy $FOLDER_ID)

  ETAG=$(echo "$POLICY_CURRENT" | yq -P '.etag')
  sed -e "s;%EXECUTIVE_GROUP%;$EXECUTIVE_GROUP;g" \
  -e "s;%BUILDER_EMAIL%;$BUILDER_EMAIL;g" \
  -e "s;%ORGANIZATION_ID%;$ORGANIZATION_ID;g" \
  -e "s;%ETAG%;$ETAG;g" folder-policy.yaml.tpl > folder-policy.yaml

  DIFF=$(diff <(yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)' folder-policy.yaml) <(echo "$POLICY_CURRENT" | yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)'))
  if ! [ -z  "$DIFF" ]; then
    echo -n 'Folder "Workspaces" policies will be updated... '
    echo "$DIFF"
    gcloud resource-manager folders set-iam-policy $FOLDER_ID folder-policy.yaml --quiet --verbosity=error
    echo 'Update completed.'
  fi
  echo "Folder \"Workspaces\" policies are up to date."
  rm -f folder-policy.yaml
}

get_tags() {
  # Create the *root* tag key
  ROOT_KEY_ID=$(gcloud resource-manager tags keys describe "$ORGANIZATION_ID/root" --format="value(name)")
  if [ $? -ne 0 ]; then
    echo -n "The \"root\" tag key will be created... "
    ROOT_KEY_ID=$(gcloud resource-manager tags keys create root --parent="organizations/$ORGANIZATION_ID" --description="root of an organization" --format="value(name)" --quiet)
    echo 'Creation completed.'
  fi
  echo "The \"root\" tag key exists with ID: $ROOT_KEY_ID"

  # Create the *workspace* tag key
  WORKSPACE_KEY_ID=$(gcloud resource-manager tags keys describe "$ORGANIZATION_ID/workspace" --format="value(name)")
  if [ $? -ne 0 ]; then
    echo -n "The \"workspace\" tag key will be created... "
    WORKSPACE_KEY_ID=$(gcloud resource-manager tags keys create workspace --parent="organizations/$ORGANIZATION_ID" --description="workspace name" --format="value(name)" --quiet)
    echo 'Creation completed.'
  fi
  echo "The \"workspace\" tag key exists with ID: $WORKSPACE_KEY_ID"

  POLICY_CURRENT=$(gcloud resource-manager tags keys get-iam-policy $WORKSPACE_KEY_ID)

  ETAG=$(echo "$POLICY_CURRENT" | yq -P '.etag')
  sed -e "s;%BUILDER_EMAIL%;$BUILDER_EMAIL;g" \
  -e "s;%ETAG%;$ETAG;g" tag-policy.yaml.tpl > tag-policy.yaml

  DIFF=$(diff <(yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)' tag-policy.yaml) <(echo "$POLICY_CURRENT" | yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)'))
  if ! [ -z  "$DIFF" ]; then
    echo -n 'Key tag "workspace" policies will be updated... '
    echo "$DIFF"
    gcloud resource-manager tags keys set-iam-policy $WORKSPACE_KEY_ID tag-policy.yaml --quiet --verbosity=error
    echo 'Update completed.'
  fi
  echo 'Key tag "workspace" policies are up to date.'
  rm -f tag-policy.yaml

  # Create the *true* tag value for the *root* tag key
  TRUE_VALUE_ID=$(gcloud resource-manager tags values describe "$ORGANIZATION_ID/root/true" --format="value(name)")
  if [ $? -ne 0 ]; then
    echo -n "The \"true\" tag value will be created... "
    TRUE_VALUE_ID=$(gcloud resource-manager tags values create true --parent="$ORGANIZATION_ID/root" --description="if the project is a root of an organization" --format="value(name)" --quiet)
    echo 'Creation completed.'
  fi
  echo "The \"true\" tag value exists with ID: $TRUE_VALUE_ID"

  # Bind the root project to the *root: true* tag
  BINDING=$(gcloud resource-manager tags bindings list --parent=//cloudresourcemanager.googleapis.com/projects/$PROJECT_NUMBER --format="value(tagValue)")
  if [ $? -ne 0 ] || [ "$BINDING" != "$TRUE_VALUE_ID" ]; then
    echo -n "The tag binding will be created... "
    gcloud resource-manager tags bindings create --parent=//cloudresourcemanager.googleapis.com/projects/$PROJECT_NUMBER --tag-value="$ORGANIZATION_ID/root/true"
    echo 'Creation completed.'
  fi
  echo "The tag binding for project \"$PROJECT_ID\" to \"root:true\" exists."
}

# Fetch the yq utility
get_yq

# Create the root project
get_root_project

# Create the workload identity pool
get_workload_identity_pool

# Create the builder service account
get_builder_account

# Create the Workspaces folder
get_workspaces_folder

# Tag resources
get_tags

echo -e "   -----\n   End of script\n   -----"
exit 0