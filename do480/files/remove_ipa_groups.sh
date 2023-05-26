#!/bin/bash

set -ue

echo $0

LOCATION=$(dirname $0)/../
##See https://access.redhat.com/solutions/5465541
function remove_ipa_groups(){      
   oc delete groups admins editors ipausers "trust admins"
}

remove_ipa_groups
