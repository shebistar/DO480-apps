#!/bin/sh

# Define kubeconfig
kubeconfig="--kubeconfig=/home/lab/ocp4/auth/kubeconfig"

# Wait for API to come online
until [ $(curl -k -s https://api.ocp4.example.com:6443/version?timeout=10s | jq -r '.major' | grep -v null | wc -l) -eq 1 ]
do
  echo "Waiting for ocp4 API..."
  sleep 10
done

# Begin looking for and signing CSRs to activate nodes
count=30
while [ ${count} -gt 0 ]
do
  for csr in $(oc get csr -ojson $kubeconfig | jq -r '.items[] | select(.status == {} ) | .metadata.name'); do
    oc adm certificate approve ${csr} $kubeconfig 
  done
  if [ $(oc get csr $kubeconfig | grep Approved | grep -v Issued | wc -l) -gt 0 ]; then
    echo "Waiting for certificate requests and issued certificates..."
  else
    echo "No pending/unissued certificate requests (CSR) found."
    count=$((${count}-1))
  fi
  sleep 20
done

# Begin looking for all nodes ready
count=10
nodes_cmd="oc get nodes --no-headers=true $kubeconfig"
while [ ${count} -gt 0 ]
do
  echo "Check if oc command reports cluster node status..."
  if [ $( ${nodes_cmd} | wc -l) -gt 0 ]; then
    echo "Command oc reports cluster node status..."
    if [ $( ${nodes_cmd} | grep -vP "\s+Ready" | wc -l) -eq 0 ]; then
      echo "All cluster nodes are ready."
      count=$((${count}-1))
    else
      echo "Not all cluster nodes are ready."
      sleep 20 
    fi
  fi
  sleep 20
done

# Run error pod cleanup process
oc get pods --no-headers=true $kubeconfig -A | grep -v -E 'Running|Completed' | grep -i error | while read line; do NS=$(echo "$line" | awk '{print $1}'); POD=$(echo "$line" | awk '{print $2}'); oc delete pod ${POD} -n ${NS} $kubeconfig; done
