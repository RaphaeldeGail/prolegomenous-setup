#!/bin/bash

# Initializes access to billing information for builder account
# Script should be executed by a FinOps for correct permissions

# TODO: add a budget

# Uncomment line below to track command line invocations
#set -x

echo -e "   -----\n   Start of script\n   -----"

# Check for pre-requisite variables
# BILLING_ACCOUNT
if [ -z "$BILLING_ACCOUNT" ]; then
  echo 'Please set the BILLING_ACCOUNT variable before executing this script.'
  exit 1
fi

read -r PROJECT_ID UUID PROJECT_NUMBER <<< $(gcloud projects list --filter="labels.root=true AND parent.type=organization" --format="value(PROJECT_ID,labels.uuid,projectNumber)")
BUILDER_EMAIL="builder@$PROJECT_ID.iam.gserviceaccount.com"

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

get_yq

POLICY_CURRENT=$(gcloud beta billing accounts get-iam-policy $BILLING_ACCOUNT)

ETAG=$(echo "$POLICY_CURRENT" | yq -P '.etag')
sed -e "s;%BUILDER_EMAIL%;$BUILDER_EMAIL;g" \
-e "s;%ETAG%;$ETAG;g" billing-policy.yaml.tpl > billing-policy.yaml

DIFF=$(diff <(yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)' billing-policy.yaml) <(echo "$POLICY_CURRENT" | yq -P '.bindings | sort_by(.role) | .[] | (.members |= sort)'))
if ! [ -z  "$DIFF" ]; then
echo -n 'Billing account policies will be updated... '
echo "$DIFF"
gcloud beta billing accounts set-iam-policy $BILLING_ACCOUNT billing-policy.yaml --quiet --verbosity=error
echo 'Update completed.'
fi
echo "Billing account policies are up to date."
rm -f billing-policy.yaml

echo -e "   -----\n   End of script\n   -----"
exit 0