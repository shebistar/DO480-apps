#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     features-review - DO480 Configure lab exercise script
#
# SYNOPSIS
#     features-review {start|grade|finish}
#
#        start   - prepare the system for starting the lab
#        grade  - perform grade steps
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#  * Tue Jan  12 2022 Rafa Ruiz <rruizher@redhat.com>
#   - Adding check of OCP with DynoLabs functions
#  * Tue Jan  4 2022 Rafa Ruiz <rruizher@redhat.com>
#   - Checking RHACM with playbooks
#  * Tue Oct 26 2021 Alejandro Coma <acomabon@redhat.com>
#   - original code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
features-review lab.
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

class featuresReview(OpenShift):
    """Activity class."""
    __LAB__ = "features-review"
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
        """Prepare the system for starting the lab."""
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
                "label": "Creating ManagedClusterSets and members of EMEA clusters",
                "task": self.run_playbook,
                "playbook": "ansible/common/acm_create_managedclusterset.yaml",
                "vars": {"managed_cluster_set": "emea","clusterset_member":"managed-cluster"},
                "fatal": True
            },
            {
                "label": "Creating ManagedClusterSets and members of APAC clusters",
                "task": self.run_playbook,
                "playbook": "ansible/common/acm_create_managedclusterset.yaml",
                "vars": {"managed_cluster_set": "apac","clusterset_member":"local-cluster"},
                "fatal": True
            },
            do480_steps.add_ipa_user(self, uid="fleet-searcher", givenname="John", sn="Searcher", password="redhat"),
            do480_steps.add_ipa_user(self, uid="apac-operator", givenname="Ophra", sn="Apac",password="redhat"),
            do480_steps.add_ipa_user(self, uid="emea-operator", givenname="Ophelia", sn="Emea", password="redhat"),
            do480_steps.add_ipa_group(self, name="fleet-searchers", users=["fleet-searcher"]),
            do480_steps.add_ipa_group(self, name="apac-operators", users=["apac-operator"]),
            do480_steps.add_ipa_group(self, name="emea-operators", users=["emea-operator"]),
            #ca cert not needed if I am in utility
            #{
            #    "label": "Retrieving the IPA CA certificate",
            #    "task": self.run_playbook,
            #    "playbook": "ansible/common/copy_ldap_cert.yaml"
            #},
            #steps.run_command(label="Syncing groups in RHOCP", hosts=["workstation"], command="oc adm", options="groups sync --sync-config " + this_path +  "/files/ldapsync.yaml --confirm", returns="0"),
            {
                "label": "Syncing groups in RHOCP",
                "task": self.run_playbook,
                "playbook": "ansible/common/ocp_sync_ldap_groups.yaml"
            },
            steps.run_command(label="Granting role to group EMEA on EMEA clusters", hosts=["workstation"], command="oc adm", options="policy add-cluster-role-to-group open-cluster-management:managedclusterset:admin:emea emea-operators", returns="0"),
            steps.run_command(label="Granting role to group APAC on APAC clusters", hosts=["workstation"], command="oc adm", options="policy add-cluster-role-to-group open-cluster-management:managedclusterset:admin:apac apac-operators", returns="0"),
            steps.run_command(label="Creating all namespaces and deployments", hosts=["workstation"], command=this_path + "/files/features-review/create_all_persistence.sh", options="", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Starting")

    def grade(self):
        """
        Grade lab exercise.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 hub cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat https://api.ocp4.example.com:6443", returns="0"),
            steps.run_command(label="Verifying that 'fleet-searchers' group has view cluster role", hosts=["workstation"], command="oc", options="get clusterrolebindings.authorization  view -ocustom-columns=groups:.groupNames.*", prints="fleet-searchers", failmsg="Fix the cluster roles of the 'fleet-searchers' group"),
            steps.run_command(label="Verifying connectivity to OCP4 managed cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat  https://api.ocp4-mng.example.com:6443", returns="0"),
            steps.run_command(label="Verifying that the deployment has 3 replicas in 'company-applications-5'", hosts=["workstation"], command="oc", options="get deployment mysql-finance-application -n company-applications-5 -o=jsonpath='{.status.replicas}'", prints="3", failmsg="Fix the deployment to run with 3 replicas"),
            steps.run_command(label="Verifying that the deployment has 3 replicas in 'company-applications-7'", hosts=["workstation"], command="oc", options="get deployment mysql-finance-application -n company-applications-7 -o=jsonpath='{.status.replicas}'", prints="3", failmsg="Fix the deployment to run with 3 replicas"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        ui = Console(items)
        ui.run_items(action="Grading")
        ui.report_grade()
    
    
    
    def finish(self):
        """Perform post-lab cleanup."""
        items = [
            {
                "label": "Checking lab systems",
                "task": labtools.check_host_reachable,
                "hosts": _targets,
                "fatal": True
            },
            ##remove labels
            steps.run_command(label="Verifying connectivity to OCP4 hub cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat https://api.ocp4.example.com:6443", returns="0"),
            steps.run_command(label="Removing clusterset labels from local-cluster", hosts=["workstation"], command="oc label", options="managedcluster local-cluster cluster.open-cluster-management.io/clusterset-", returns="0"),
            steps.run_command(label="Removing clusterset labels from managed-cluster", hosts=["workstation"], command="oc label", options="managedcluster managed-cluster cluster.open-cluster-management.io/clusterset-", returns="0"),
            ##remove managedclustersets
            steps.run_command(label="Removing clusterset apac ", hosts=["workstation"], command="oc delete", options="managedclustersets apac", returns="0"),
            steps.run_command(label="Removing clusterset emea ", hosts=["workstation"], command="oc delete", options="managedclustersets emea", returns="0"),
            
            ##IdM
            do480_steps.remove_ipa_user(self, uid="fleet-searcher"),
            do480_steps.remove_ipa_user(self, uid="apac-operator"),
            do480_steps.remove_ipa_user(self, uid="emea-operator"),
            
            
            do480_steps.remove_ipa_group(self, name="fleet-searchers"),
            do480_steps.remove_ipa_group(self, name="apac-operators"),
            do480_steps.remove_ipa_group(self, name="emea-operators"),
            #ca cert not needed if I am in utility
            {
                "label": "Syncing groups in RHOCP",
                "task": self.run_playbook,
                "playbook": "ansible/common/ocp_sync_ldap_groups.yaml"
            },
            steps.run_command(label="Deleting all namespaces and deployments. This command takes a while. Do not interrupt the execution.", hosts=["workstation"], command=this_path + "/files/features-review/delete_all_persistence.sh", options="", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Finishing")
