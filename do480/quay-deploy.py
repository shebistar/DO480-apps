#
# Copyright 2022 Red Hat, Inc.
#
# NAME
#     quay-deploy - DO480 Configure lab exercise script
#
# SYNOPSIS
#     quay-deploy {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#   * Fri May 13 2022 Rafa Ruiz <rruizher@redhat.com>
#   - Corrected to run IdM commands frojm utility
#   * Mon Apr 11 2022 Rafa Ruiz <rruizher@redhat.com>
#   - initial code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
quay-deploy guided exercise.
"""

import os
import sys
import logging
import pkg_resources
import requests
import yaml

from .common import steps
from urllib3.exceptions import InsecureRequestWarning
from ocp import api
from ocp.utils import OpenShift
from labs import labconfig
from labs.common.userinterface import Console
from labs.common import labtools
from labs.grading import Default as GuidedExercise
from kubernetes.client.exceptions import ApiException
from .common.constants import USER_NAME, IDM_SERVER, OCP4_API, OCP4_MNG_API
from do480 import do480_steps

SKU = labconfig.get_course_sku().upper()
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost","workstation"]

class QuayDeploy(OpenShift):
    """Activity class."""
    __LAB__ = "quay-deploy"
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
            
            
        
            do480_steps.add_ipa_user(self, uid="cloudadmin", givenname="Superadmin", sn="Superadmin", password="redhat"),
            do480_steps.add_ipa_group(self, name="admins", users=["admin","cloudadmin"]),
            ##Cluster 1
            steps.run_command(label="Login in RHOCP", hosts=["workstation"], command="oc", options="login -u admin -p redhat " + OCP4_API, returns="0"),
            {
                "label": "Syncing groups in hub RHOCP and managed clusters",
                "task": self.run_playbook,
                "playbook": "ansible/common/ocp_sync_ldap_groups.yaml"
            },
            steps.run_command(label="Add cluster role for cloudadmins", hosts=["workstation"], command="oc adm", options="policy add-cluster-role-to-group cluster-admin admins", returns="0"),
            steps.run_command(label="Creating user cloudadmin in RHOCP", hosts=["workstation"], command="oc", options="login -u cloudadmin -p redhat https://api.ocp4.example.com:6443", returns="0"),
            
            ##Cluster 2
            steps.run_command(label="Login in managed RHOCP", hosts=["workstation"], command="oc", options="login -u admin -p redhat https://api.ocp4-mng.example.com:6443", returns="0"),
            
            steps.run_command(label="Login in managed RHOCP", hosts=["workstation"], command="oc", options="login -u admin -p redhat https://api.ocp4-mng.example.com:6443", returns="0"),
            steps.run_command(label="Add cluster role for cloudamins", hosts=["workstation"], command="oc adm", options="policy add-cluster-role-to-group cluster-admin admins", returns="0"),
            steps.run_command(label="Creating user cloudadmin in managed RHOCP", hosts=["workstation"], command="oc", options="login -u cloudadmin -p redhat https://api.ocp4-mng.example.com:6443", returns="0"),

            {
                "label": "Ensuring that Quay registry and the Quay operator are not present. This command can take more than 5 minutes. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_remove.yaml"
            },
            {
                "label": "Copy exercise files",
                "task": labtools.copy_lab_files,
                "lab_name": self.__LAB__,
                "fatal": True
            },
            {
                "label": "Retrieving the IPA CA certificate",
                "task": self.run_playbook,
                "playbook": "ansible/common/copy_ldap_cert.yaml"
            },
            steps.run_command(label="Copying IPA CA certificate for the materials", hosts=["workstation"],command="cp", options="/home/student/ca.crt /home/student/DO480/labs/quay-deploy/ldap.crt", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Starting")

    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            
            steps.run_command(label="Login in RHOCP", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            ##If we want to clean users, we need to delete the User object and the Identity object. See https://access.redhat.com/solutions/5465541
            do480_steps.remove_ipa_user(self, uid="cloudadmin"),
            steps.run_command(label="Delete cloudadmin user", hosts=["workstation"], command=this_path + "/files/remove_user_and_identity.sh cloudadmin", options="", returns="0"),
            steps.run_command(label="Login in managed RHOCP", hosts=["workstation"], command="oc", options="login -u admin -p redhat https://api.ocp4-mng.example.com:6443", returns="0"),
            steps.run_command(label="Delete cloudadmin user in all clusters", hosts=["workstation"], command=this_path + "/files/remove_user_and_identity.sh cloudadmin", options="", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Finishing")
