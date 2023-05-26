#!/bin/bash

set -ue

echo $0

LOCATION=$(dirname $0)/../

# populate cluster
# first arg api_url
# second arg parameter for the mistake in 'persistence5'
function populate_cluster(){
  
  #app_names=(finance marketing humanresources globalshop)
  app_names=(finance-application-1 finance-application-2 finance-application-3 finance-application-4 marketing-application-1 marketing-application-2 humanresources-application-1 humanresources-application-2 globalshop-application) 
  oc login -u admin -p redhat $1 
  while [ $NS_NUMBER -ge 1 ]
  do
   
    app_name=${app_names[RANDOM%${#app_names[@]}]} 
       
    oc new-project "company-applications-$NS_NUMBER"
  
    if [ $NS_NUMBER -eq 5 ]
    then
      oc process -f ${LOCATION}/features-console/mysql-enterprise-persistence.yaml -p "CLAIM_NAME=nonexistingdbclaim" -p "APPLICATION=finance-application-2"| oc create -f -
    elif [ $NS_NUMBER -eq 6 ]
    then 
      oc process -f ${LOCATION}/features-console/mysql-enterprise-persistence.yaml -p "MYSQL_IMAGE=registry.redhat.io/rhel8/mysql-80:1-127" -p "APPLICATION=globalshop-application"| oc create -f -
      #oc process -f my-enterprise-persistence.yaml -p "MYSQL_IMAGE=docker.io/library/mysql:8.0" | oc create -f -
      #oc process -f my-enterprise-persistence.yaml -p "MYSQL_IMAGE=quay.io/centos7/mysql-80-centos7:8.0" -p "APPLICATION=$ns_name"| oc create -f -
      
    else
      echo "The app name: $app_name"
  
      case $app_name in
      
        finance-application-1 | finance-application-3 | finance-application-4 | humanresources-application-2 | marketing-application-1 )
          oc process -f ${LOCATION}/features-console/postgresql-enterprise-persistence.yaml -p "APPLICATION=$app_name"| oc create -f -
          ;;
          
        finance-application-2 | globalshop-application )
          oc process -f ${LOCATION}/features-console/mysql-enterprise-persistence.yaml -p "APPLICATION=$app_name"| oc create -f -
          ;;
        
        humanresources-application-1 | marketing-application-2 )
          oc process -f ${LOCATION}/features-console/mariadb-enterprise-persistence.yaml -p "APPLICATION=$app_name"| oc create -f -
         
          ;;
        *)
          echo "No Matches"
          ;;
      esac
      
    fi 
    ((NS_NUMBER--))
  done

}
NS_NUMBER=15 && populate_cluster "https://api.ocp4.example.com:6443" && NS_NUMBER=15 && populate_cluster "https://api.ocp4-mng.example.com:6443"
