#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     policy-gatekeeper - DO480 Configure lab exercise script
#
# SYNOPSIS
#     policy-gatekeeper {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#   * Tue 07 Dec 2021 Harpal Singh <harpasin@redhat.com>
#   - original code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
policy-gatekeeper guided exercise.
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
from labs.common import labtools
from labs.common.userinterface import Console
from labs.grading import Default as GuidedExercise
from kubernetes.client.exceptions import ApiException
from .common.constants import USER_NAME, IDM_SERVER, OCP4_API, OCP4_MNG_API

SKU = labconfig.get_course_sku().upper()

labname = 'policy-gatekeeper'
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost", "workstation"]

class PolicyCompliance(OpenShift):
    """
    policy-gatekeeper lab script for DO480
    """
    __LAB__ = "policy-gatekeeper"

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
            print("The Lab environment is not ready, please wait 10 minutes before trying again")
            sys.exit(1)
        except ApiException:
            print("The OpenShift cluster is not ready, please wait 5 minutes before trying again ")
            sys.exit(1)
        except Exception:
            print("An unknown error ocurred")
            logging.exception("An unknown error ocurred")
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
            steps.run_command(label="Logging in to OCP4 managed cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_MNG_API, returns="0"),
            steps.run_command(label="Project `openshift-gatekeeper-system` is not present in managed-cluster", hosts=["workstation"], command="oc", options="get projects openshift-gatekeeper-system", returns="1", failmsg="The openshift-gatekeeper-system Project already exists, please delete it or run 'lab finish policy-gatekeeper' before starting this GE"),
            steps.run_command(label="Logging in to OCP4 hub cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            steps.run_command(label="Adding environment label to managed-cluster", hosts=["workstation"], command="oc", options="label managedclusters managed-cluster environment=production --overwrite", prints="managed-cluster"),
            steps.run_command(label="Adding environment label to local-cluster", hosts=["workstation"], command="oc", options="label managedclusters local-cluster environment=stage --overwrite", prints="local-cluster"),
            {
                "label": "Project 'policy-gatekeeper' is not present",
                "task": self._fail_if_exists,
                "name": "policy-gatekeeper",
                "type": "Project",
                "api": "project.openshift.io/v1",
                "namespace": "",
                "fatal": True
            },
            {
                "label": "Project 'openshift-gatekeeper-system' is not present in local-cluster",
                "task": self._fail_if_exists,
                "name": "openshift-gatekeeper-system",
                "type": "Project",
                "api": "project.openshift.io/v1",
                "namespace": "",
                "fatal": True
            },
            {
                "label": "Project 'app-stage' is not present",
                "task": self._fail_if_exists,
                "name": "app-stage",
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
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Starting")

    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            {
                "label": "Removing the policy-gatekeeper namespace",
                "task": self._delete_resource,
                "kind": "Project",
                "api": "project.openshift.io/v1",
                "name": "policy-gatekeeper",
                "namespace": None,
            },
            {
                "label": "Removing the openshift-gatekeeper-system namespace",
                "task": self._delete_resource,
                "kind": "Project",
                "api": "project.openshift.io/v1",
                "name": "openshift-gatekeeper-system",
                "namespace": None,
            },
            {
                "label": "Removing the app-stage namespace",
                "task": self._delete_resource,
                "kind": "Project",
                "api": "project.openshift.io/v1",
                "name": "app-stage",
                "namespace": None,
            },
            steps.run_command(label="Removing production environment label", hosts=["workstation"], command="oc", options="label managedclusters managed-cluster environment- --overwrite", returns="0"),
            steps.run_command(label="Removing stage environment label", hosts=["workstation"], command="oc", options="label managedclusters local-cluster environment- --overwrite", returns="0"),
            steps.run_command(label="Verifying connectivity to OCP4 managed cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_MNG_API, returns="0"),
            steps.run_command(label="Removing namespaces", hosts=["workstation"], command=this_path + "/files/policy-gatekeeper/delete_project.sh", options="", returns="0"),
            steps.run_command(label="Removing gatekeeper operator", hosts=["workstation"], command=this_path + "/files/policy-gatekeeper/remove_gatekeeper.sh", options="", returns="0"),
            {
                "label": "Remove lab files",
                "task": labtools.delete_workdir,
                "lab_name": self.__LAB__,
                "fatal": True
            },
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
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
