#!/bin/bash

set -ue

echo $0

LOCATION=$(dirname $0)/../
##See https://access.redhat.com/solutions/5465541
function remove_user_and_its_identity(){   
   useridentity=$(oc get identities | grep $1 |awk -F"  " '{print $1}')   
   oc delete user $1 && oc delete identity "$useridentity"      
}

remove_user_and_its_identity $1
