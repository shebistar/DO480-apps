#!/bin/bash

set -ue

echo $0


##Creates 1 namespace  with one deployment pulling from a public registry
function populate_clusters(){
  oc login -u admin -p redhat https://api.ocp4.example.com:6443
  oc create namespace budget-app
  oc process -f /home/student/DO480/labs/quayacm-restrict/template-app-deployment.yaml -p "APPLICATION=budget-app"| oc create -n budget-app -f -
}

populate_clusters