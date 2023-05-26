#!/bin/bash

playbook_dir="/home/student/DO480/labs/policy-governance/ansible"
cert_name="wildcard"
combined_name="wildcard-combined"
this='policy-governance'

  sudo ansible-playbook ${playbook_dir}/classroom-ca.yml
  sudo ansible-playbook ${playbook_dir}/wildcard.yml -e cert_path=/home/student/DO480/labs/${this} -e "not_after=+100h" -e update_cert=True -e combined_name=${combined_name}
    # Check for existing 'wildcard-bundle' configuration map
    if oc get configmap/wildcard-bundle -n openshift-config
    then
      oc extract configmap/wildcard-bundle -n openshift-config --to=/tmp/ --confirm
      if ! diff /tmp/ca-bundle.crt /etc/pki/tls/certs/wildcard-combined.pem
      then
        oc set data configmap/wildcard-bundle -n openshift-config --from-file=ca-bundle.crt=/etc/pki/tls/certs/wildcard-combined.pem
      fi
      rm -f /tmp/ca-bundle.crt
    else
      # Create configmap in openshift-config
      oc create configmap wildcard-bundle --from-file=ca-bundle.crt=/etc/pki/tls/certs/wildcard-combined.pem -n openshift-config
    fi
    # Patch proxy/cluster
    oc patch proxy/cluster --type=merge --patch='{"spec":{"trustedCA":{"name":"wildcard-bundle"}}}'
    # Check for existing 'wildcard-tls' secret
    if oc get secret/wildcard-tls -n openshift-ingress
    then
      oc extract secret/wildcard-tls -n openshift-ingress --to=/tmp/ --confirm
      if ! diff /tmp/tls.crt /etc/pki/tls/certs/wildcard-combined.pem
      then
        oc set data secret/wildcard-tls -n openshift-ingress --from-file=tls.crt=/etc/pki/tls/certs/wildcard-combined.pem --from-file=tls.key=/etc/pki/tls/private/wildcard-key.pem
      fi
      rm -rf /tmp/tls.crt /tmp/tls.key
    else
      # Create secret in openshift-ingress
      oc create secret tls wildcard-tls --cert=/etc/pki/tls/certs/wildcard-combined.pem --key=/etc/pki/tls/private/wildcard-key.pem -n openshift-ingress
    fi
    # Patch ingresscontroller/default
    oc patch ingresscontroller.operator/default -n openshift-ingress-operator --type=merge --patch='{"spec":{"defaultCertificate":{"name":"wildcard-tls"}}}'
  

  
  # There may be router pods in a failed phase with a reason of MatchNodeSelector.
  # Delete those pods if they exist.
  for POD in $(oc get pods -o name -n openshift-ingress)
  do
    POD_STATUS="$(oc get ${POD} -n openshift-ingress -o jsonpath='{.status.phase}')"
    if [ "${POD_STATUS}" == "Failed" ]
    then
      oc delete ${POD} -n openshift-ingress
    fi
  done
