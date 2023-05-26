#!/bin/bash

set -ue

function delete_namespaces(){
 oc login -u admin -p redhat $1
 oc get namespaces --no-headers=true -o custom-columns=:metadata.name| grep 'company-application' | xargs oc delete namespace
}

delete_namespaces "https://api.ocp4.example.com:6443"

delete_namespaces "https://api.ocp4-mng.example.com:6443"
