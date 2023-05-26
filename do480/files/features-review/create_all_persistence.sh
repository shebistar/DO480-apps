#!/bin/bash

set -ue

echo $0

LOCATION=$(dirname $0)/../

# populate cluster for review lab
# first arg api_url
# second arg parameter for the mistake in 'persistence5'
function populate_cluster(){
  
  #app_names=(finance marketing humanresources globalshop)
  app_names=(finance-application) 
  oc login -u admin -p redhat $1 
  while [ $NS_NUMBER -ge 1 ]
  do
   
    app_name=${app_names[RANDOM%${#app_names[@]}]} 
       
    oc new-project "company-applications-$NS_NUMBER"
  
    if [[ ( $NS_NUMBER -eq 5 || $NS_NUMBER -eq 7 )  &&  $1 == https://api.ocp4-mng.example.com:6443 ]]
    then
      #different storageclass to allow resizing. No. Cannot search in 'local-cluster'
      #oc process -f ${LOCATION}/features-review/mysql-enterprise-persistence.yaml -p "PVC_SIZE=25Mi" -p "STORAGE_CLASS=ocs-external-storagecluster-cephfs" -p "APPLICATION=finance-application-2"| oc create -f -
      oc process -f ${LOCATION}/features-review/mysql-enterprise-persistence.yaml -p "REPLICAS=1" -p "APPLICATION=finance-application"| oc create -f -
    else
      echo "The app name: $app_name"
      oc process -f ${LOCATION}/features-review/mysql-enterprise-persistence.yaml -p "APPLICATION=$app_name"| oc create -f -
    fi 
    ((NS_NUMBER--))
  done

}
NS_NUMBER=15 && populate_cluster "https://api.ocp4.example.com:6443" && NS_NUMBER=15 && populate_cluster "https://api.ocp4-mng.example.com:6443"
