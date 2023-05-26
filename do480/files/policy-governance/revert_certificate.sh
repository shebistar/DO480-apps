#!/bin/bash

oc login -u admin -p redhat https://api.ocp4-mng.example.com:6443 --insecure-skip-tls-verify

oc patch ingresscontroller.operator/default --type=merge --patch='{"spec":{"defaultCertificate":{"name":"classroom-tls"}}}' -n openshift-ingress-operator

if oc get secret/wildcard-tls -n openshift-ingress
then
   oc delete secret wildcard-tls -n openshift-ingress
fi

oc patch proxy/cluster --type=merge --patch='{"spec":{"trustedCA":{"name":"classroom-certs"}}}'

if oc get configmap/wildcard-bundle -n openshift-config
then
   oc delete configmap wildcard-bundle -n openshift-config
fi