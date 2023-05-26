#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     quayacm-review - DO480 Configure lab exercise script
#
# SYNOPSIS
#     quayacm-review {start|grade|finish}
#
#        start   - prepare the system for starting the lab
#        grade   - grades the lab
#        finish  - perform post-exercise cleanup steps

import os
import sys
import logging
import pkg_resources
import requests
import subprocess
#Thanks to Alex. Back to from labs.common import steps
from labs.common import steps
#from .common import steps
from ocp.utils import OpenShift
from labs import labconfig
from labs.common.userinterface import Console
from labs.common import labtools
from kubernetes.client.exceptions import ApiException
from .common.constants import USER_NAME, IDM_SERVER, OCP4_API, OCP4_MNG_API

SKU = labconfig.get_course_sku().upper()
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost","workstation"]

class QuayacmReview(OpenShift):
    """Activity class."""
    __LAB__ = "quayacm-review"
    # Get the OCP host and port from environment variables
    OCP_API = {
        "user": os.environ.get("OCP_USER", "admin"),
        "password": os.environ.get("OCP_PASSWORD", "redhat"),
        "host": os.environ.get("OCP_HOST", "api.ocp4.example.com"),
        "port": os.environ.get("OCP_PORT", "6443"),
    }

    OCP_MNG_API = {
        "user": os.environ.get("OCP_USER", "admin"),
        "password": os.environ.get("OCP_PASSWORD", "redhat"),
        "host": os.environ.get("OCP_HOST", "api.ocp4-mng.example.com"),
        "port": os.environ.get("OCP_PORT", "6443"),
    }
    
    # Initialize class
    def __init__(self):
        logging.debug("{} / {}".format(SKU, sys._getframe().f_code.co_name))
        try:
            super().__init__()
        except requests.exceptions.ConnectionError:
            print("The Lab environment is not ready, please wait 10 minutes before trying again.")
            sys.exit(1)
        except ApiException:
            print("The OpenShift cluster is not ready, please wait 5 minutes before trying again.")
            sys.exit(1)
        except Exception as e:
            print("An unknown error ocurred: " + str(e))
            logging.exception("An unknown error ocurred: " + str(e))
            sys.exit(1)
    
    def start(self):
        """
        Prepare systems for the lab exercise.
        """
        items = [
            {
                "label": "Checking lab systems",
                "task": labtools.check_host_reachable,
                "hosts": _targets,
                "fatal": True
            },
            {
                "label": "Checking that the OCP hub is up and ready",
                "task": self.run_playbook,
                "playbook": "ansible/common/ocp_cluster_up_and_ready.yaml",
                "fatal": True
            },
            {
                "label": "Checking that RHACM is installed. Installing if needed. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/acm_install.yaml",
                "fatal": True
                
            },
            {
                "label": "Checking that MulticlusterHub is deployed. Deploying if needed. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/acm_create_multiclusterhub.yaml",
                "fatal": True
                
            },
            {
                "label": "Importing the managed clusters. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/acm_import_cluster2.yaml",
                "fatal": True
                
            },
            {
                "label": "Removing Quay CRD. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_remove.yaml",
                "vars": {"remove_quay_operator": False,}
            },
            {
                "label": "Installing Quay. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_install.yaml",
                "vars": {"quay_auth_type": "database",}
            },
            {
                "label": "Copy exercise files",
                "task": labtools.copy_lab_files,
                "lab_name": self.__LAB__,
                "fatal": True
            },

            steps.run_command(label="Creating Quay resources", hosts=["workstation"], command=this_path + "/files/quayacm-review/create_quay_resources.sh", shell=True, returns="0"),
            #Tag clusters
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_API, returns="0", shell=True),
            steps.run_command(label="Tagging production clusters", hosts=["workstation"], command="oc label managedcluster managed-cluster env=production --overwrite", shell=True, returns="0"),
            steps.run_command(label="Restoring the image controller object in managed clusters", hosts=["workstation"], command=this_path + "/files/quayacm-restrict/restore_image_object.sh", shell=True, returns="0"),
            steps.run_command(label="Login in managed clusters", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_MNG_API, shell=True, returns="0"),
            steps.run_command(label="Removing budget-app namespace", hosts=["workstation"], command=this_path + "/files/quayacm-review/delete_project.sh", shell=True, returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc logout", returns="0", shell=True)
        ]
        Console(items).run_items(action="Starting")

    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_API, returns="0", shell=True),
            steps.run_command(label="Untagging production clusters", hosts=["workstation"], command="oc label managedcluster managed-cluster env-", returns="0", shell=True),
            {
                "label": "Removing Quay. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_remove.yaml",
            },
            {
                "label": "Remove lab files",
                "task": labtools.delete_workdir,
                "lab_name": self.__LAB__,
                "fatal": True
            },
            {
                "label": "Removing the image policy",
                "task": self._delete_resource,
                "kind": "Policy",
                "api": "policy.open-cluster-management.io/v1",
                "name": "image-policy",
                "namespace": "policies",
            },
            {
                "label": "Removing the policies namespace",
                "task": self._delete_resource,
                "kind": "Project",
                "api": "project.openshift.io/v1",
                "name": "policies",
                "namespace": None,
            },
            {
                "label": "Removing the budget-app namespace",
                "task": self._delete_resource,
                "kind": "Project",
                "api": "project.openshift.io/v1",
                "name": "budget-app",
                "namespace": None,
            },
            steps.run_command(label="Removing robot secret file", hosts=["workstation"], command="rm -f /home/student/Downloads/finance-prod-deployer-secret.yml", returns="0", shell=True),
            steps.run_command(label="Removing token file", hosts=["workstation"], command="rm -f /home/student/prod_deployer_token", returns="0", shell=True),
            steps.run_command(label="Removing container file", hosts=["workstation"], command="rm -f /home/student/Containerfile", returns="0", shell=True),
            steps.run_command(label="Restoring the image controller object in managed clusters", hosts=["workstation"], command=this_path + "/files/quayacm-restrict/restore_image_object.sh", shell=True, returns="0"),
            steps.run_command(label="Login in managed clusters", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_MNG_API, shell=True, returns="0"),
            steps.run_command(label="Removing budget-app namespace", hosts=["workstation"], command=this_path + "/files/quayacm-review/delete_project.sh", shell=True, returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc logout", returns="0", shell=True)
        ]
        Console(items).run_items(action="Finishing")

    def grade(self):
        """
        Grade lab exercise.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_API, returns="0", shell=True),
            steps.run_command(label="Verifying budget-app namespace exists", hosts=["workstation"], command="oc get namespace budget-app", returns="0", shell=True),
            steps.run_command(label="Verifying connectivity to managed clusters", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_MNG_API, returns="0", shell=True),
            steps.run_command(label="Verifying budget-app namespace exists in managed clusters", hosts=["workstation"], command="oc get namespace budget-app", returns="0", shell=True),
            steps.run_command(label="Check that the /home/student/prod_deployer_token file exists", hosts=["workstation"], command="test -f /home/student/prod_deployer_token", returns="0", shell=True),
            steps.run_command(label="Log in to production cluster", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_MNG_API, returns="0", shell=True),
            steps.run_command(label="Verifying that the image policy is applied in production clusters and contains the central quay registry image", hosts=["workstation"], command="oc get image.config.openshift.io cluster -o json | jq .spec.registrySources.allowedRegistries | grep 'budget-app:production'", returns="0", shell=True),
            steps.run_command(label="Verifying that the budget-app is running in production clusters", hosts=["workstation"], command="oc get deployment budget-app -n budget-app -o json | jq .status.readyReplicas | grep 1", returns="0", shell=True)
        ]
        ui = Console(items)
        ui.run_items(action="Grading")
        ui.report_grade()

    def _delete_resource(self, item):
        item["failed"] = False
        try:
            self.delete_resource(
                item["api"],
                item["kind"],
                item["name"],
                item["namespace"]
            )
        except Exception as e:
            item["failed"] = True
            item["msgs"] = [
                {"text": "Failed removing %s: %s" % (item["kind"], e)}
            ]
            logging.debug(e)
