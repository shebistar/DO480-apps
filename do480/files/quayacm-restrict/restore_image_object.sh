#!/bin/bash

set -ue

echo $0

LOCATION=$(dirname $0)/../

function patch_image {
  oc patch image.config.openshift.io/cluster --type=json -p '[{"op":"replace","path":"/spec","value": {}}]'
}


oc login -u admin -p redhat https://api.ocp4.example.com:6443
patch_image
sleep 2
oc login -u admin -p redhat https://api.ocp4-mng.example.com:6443
patch_image
