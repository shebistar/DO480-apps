#!/bin/bash

set -ue

echo $0

LOCATION=$(dirname $0)/../


echo "Getting token"

ACCESS_TOKEN=$(curl -X POST -k  https://central-quay-registry.apps.ocp4.example.com/api/v1/user/initialize --header 'Content-Type: application/json' --data '{ "username": "cloudadmin", "password":"redhat123", "email": "cloudadmin@ocp4.example.com", "access_token": true}' | jq -r '.access_token')

#Create finance org
echo "Create finance org and repo"
curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Content-Type: application/json' -d '{"name":"finance","email":"finance@ocp4.example.com"}' https://central-quay-registry.apps.ocp4.example.com/api/v1/organization/

#Create budget-app empty repo
curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '
{"namespace":"finance","repository":"budget-app","description":"Repo for the Budget production application","visibility":"private"}' https://central-quay-registry.apps.ocp4.example.com/api/v1/repository

#Create budget-app-dev repo with the image
curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '
{"namespace":"finance","repository":"budget-app-dev","description":"Repo for the Budget application Finance development team","visibility":"private"}' https://central-quay-registry.apps.ocp4.example.com/api/v1/repository

#Create the image

echo "FROM quay.io/redhattraining/hello-world-nginx:v1.0" > Containerfile
podman build . -t budget-app-dev:1.0


#Copy image to the repository
echo "Copying image"
podman login -u=cloudadmin -p=redhat123 central-quay-registry.apps.ocp4.example.com

podman push localhost/budget-app-dev:1.0 central-quay-registry.apps.ocp4.example.com/finance/budget-app-dev:1.0
rm Containerfile


