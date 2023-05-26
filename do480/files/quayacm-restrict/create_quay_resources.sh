#!/bin/bash

set -ue

echo $0

LOCATION=$(dirname $0)/../

##Create admin user and getting token:
ACCESS_TOKEN=$(curl -X POST -k  https://central-quay-registry.apps.ocp4.example.com/api/v1/user/initialize --header 'Content-Type: application/json' --data '{ "username": "admin", "password":"redhat123", "email": "admin@ocp4.example.com", "access_token": true}' | jq -r '.access_token')

#Create finance and public orgs

curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Content-Type: application/json' -d '{"name":"finance","email":"finance@ocp4.example.com"}' https://central-quay-registry.apps.ocp4.example.com/api/v1/organization/

curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Content-Type: application/json' -d '{"name":"public","email":"public@ocp4.example.com"}' https://central-quay-registry.apps.ocp4.example.com/api/v1/organization/



#Create 2 public repos org with the mysql image
curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '
{"namespace":"finance","repository":"approved-mysql","description":"Repo for images from the Finance development team","visibility":"public"}' https://central-quay-registry.apps.ocp4.example.com/api/v1/repository

curl -X POST -H "Authorization: Bearer ${ACCESS_TOKEN}" -H "Content-Type: application/json" -d '
{"namespace":"public","repository":"mysql","description":"Repo for public tools images","visibility":"public"}' https://central-quay-registry.apps.ocp4.example.com/api/v1/repository

#Copy mysql image to both repositories
skopeo login -u=admin -p=redhat123 central-quay-registry.apps.ocp4.example.com

skopeo copy docker://quay.io/centos7/mysql-80-centos7:latest docker://central-quay-registry.apps.ocp4.example.com/public/mysql:8.0

skopeo copy docker://central-quay-registry.apps.ocp4.example.com/public/mysql:8.0 docker://central-quay-registry.apps.ocp4.example.com/finance/approved-mysql:8.0