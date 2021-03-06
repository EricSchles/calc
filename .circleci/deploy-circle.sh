#!/bin/bash

# DEPLOY_ENV must be set to "dev", "staging", or "prod"

# CF_DEV_USER, CF_STAGING_USER, CF_PROD_USER, and the associated
# CF_DEV_PASSWORD, CF_STAGING_PASSWORD, and CF_PROD_PASSWORD
# are defined as private Environment Variables
# in the CircleCI web UI: https://circleci.com/gh/18F/calc/edit#env-vars

set -e

if [ "$DEPLOY_ENV" == "dev" ]; then
  DEPLOY_USER=$CF_DEV_USER
  DEPLOY_PASS=$CF_DEV_PASSWORD
  SPACE=dev
elif [ "$DEPLOY_ENV" == "staging" ]; then
  DEPLOY_USER=$CF_STAGING_USER
  DEPLOY_PASS=$CF_STAGING_PASSWORD
  SPACE=staging
elif [ "$DEPLOY_ENV" == "prod" ]; then
  DEPLOY_USER=$CF_PROD_USER
  DEPLOY_PASS=$CF_PROD_PASSWORD
  SPACE=prod
else
  echo "Branch does not trigger a deployment. Exiting."
  exit 1
fi

API="https://api.fr.cloud.gov"
ORG="fas-calc"

APP_NAME="calc-$DEPLOY_ENV"
MANIFEST="manifests/manifest-$DEPLOY_ENV.yml"

# make a production build
unset DEBUG
yarn gulp -- build

# install cf cli
curl -L -o cf-cli_amd64.deb 'https://cli.run.pivotal.io/stable?release=debian64&source=github'
sudo dpkg -i cf-cli_amd64.deb
rm cf-cli_amd64.deb

# install autopilot
cf install-plugin autopilot -f -r CF-Community

echo "Deploying to $SPACE space."

cf login -a $API -u $DEPLOY_USER -p $DEPLOY_PASS -o $ORG -s $SPACE

# scale down the app instances to avoid overrunning our memory allotment
cf scale -i 1 $APP_NAME

cf zero-downtime-push $APP_NAME -f $MANIFEST
