#
# Copyright 2022 Red Hat, Inc.
#
# NAME
#     quayacm-restrict - DO480 Configure lab exercise script
#
# SYNOPSIS
#      quayacm-restrict {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#   * Thu Jun 30 2022 Rafa Ruiz <rruizher@redhat.com>
#   - Corrections to finish verb after E2E qa.
#   * Fri May 17 2022 Rafa Ruiz <rruizher@redhat.com>
#   - initial code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
quay-restrict guided exercise.
"""

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

class QuayacmRestrict(OpenShift):
    """Activity class."""
    __LAB__ = "quayacm-restrict"
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
                "vars": {"remove_quay_operator": False,},
            },
            {
                "label": "Installing Quay. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_install.yaml",
                "vars": {"quay_auth_type": "database",},
                
            },
            {
                "label": "Project 'policies' is not present",
                "task": self._fail_if_exists,
                "name": "policies",
                "type": "Project",
                "api": "project.openshift.io/v1",
                "namespace": "",
                "fatal": True
            },
            {
                "label": "Copy exercise files",
                "task": labtools.copy_lab_files,
                "lab_name": self.__LAB__,
                "fatal": True
            },

            ##create 2 public quay repos for mysql, one is allowed, the other is not. Auth is database to access oauth token
            steps.run_command(label="Creating Quay resources", hosts=["workstation"], command=this_path + "/files/quayacm-restrict/create_quay_resources.sh", shell=True, returns="0"),
            steps.run_command(label="Creating insecure deployments", hosts=["workstation"], command=this_path + "/files/quayacm-restrict/create_insecure_deployments.sh", shell=True, returns="0"),
            steps.run_command(label="Restoring the image controller object in managed clusters", hosts=["workstation"], command=this_path + "/files/quayacm-restrict/restore_image_object.sh", shell=True, returns="0"),
            steps.run_command(label="Login in managed clusters", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_MNG_API, shell=True, returns="0"),
            steps.run_command(label="Removing invoices-app namespaces", hosts=["workstation"], command=this_path + "/files/quayacm-restrict/delete_project.sh", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc logout", shell=True, returns="0")
        ]
        Console(items).run_items(action="Starting")

    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            steps.run_command(label="Login in RHOCP", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_API, shell=True, returns="0"),
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
            steps.run_command(label="Restoring the image controller object in managed clusters", hosts=["workstation"], command=this_path + "/files/quayacm-restrict/restore_image_object.sh", shell=True, returns="0"),
            steps.run_command(label="Login in managed clusters", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_MNG_API, shell=True, returns="0"),
            steps.run_command(label="Removing invoices-app namespaces", hosts=["workstation"], command=this_path + "/files/quayacm-restrict/delete_project.sh", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc logout", shell=True, returns="0"),
            {
                    "label": "Remove lab files",
                    "task": labtools.delete_workdir,
                    "lab_name": self.__LAB__,
                    "fatal": True
            },
        ]
        Console(items).run_items(action="Finishing")
    
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
