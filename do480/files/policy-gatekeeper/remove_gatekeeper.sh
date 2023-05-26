#!/bin/bash

function delete_sub(){
 oc login -u admin -p redhat $1
 oc delete gatekeepers.operator.gatekeeper.sh gatekeeper
 if oc get subscriptions.operators.coreos.com/gatekeeper-operator-product -n openshift-operators
 then
   oc delete subscriptions.operators.coreos.com/gatekeeper-operator-product -n openshift-operators
 fi

 
 csvop=$(oc get csv -n openshift-operators -o name | grep gatekeeper)
 if [ "$csvop" ]
 then
   oc delete $csvop -n openshift-operators
 fi
}

delete_sub "https://api.ocp4.example.com:6443"

delete_sub "https://api.ocp4-mng.example.com:6443"



