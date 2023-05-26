#!/bin/bash

function delete_project {
  local project="$1"

  while [ "${project}" != "" ]
  do

    if oc get project "${project}"
    then
      local project_status="$(oc get namespace ${project} -o jsonpath='{.status.phase}')"
      if [ "${project_status}" == "Active" ]
      then
        if oc delete project "${project}" --wait=true
        then
          local RETRIES=20
          while [ "${RETRIES}" != 0 ]; do
            sleep 3
            if oc get project "${project}" -o name
            then
              true
            else
              break
            fi
            let RETRIES=RETRIES-1
          done
        fi
      fi
    fi
    
    shift
    project="$1"
  done
}

delete_project "invoices-app"
