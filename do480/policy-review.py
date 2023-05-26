#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     policy-review - DO480 Configure lab exercise script
#
# SYNOPSIS
#     policy-review {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#   * Thu 20 Jan 2022 Harpal Singh <harpasin@redhat.com>
#   - Adding grading script for policies
#   * Mon 17 Jan 2022 Harpal Singh <harpasin@redhat.com>
#   - original code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
policy-review guided exercise.
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

SKU = labconfig.get_course_sku().upper()

labname = 'policy-review'
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost","workstation"]

class PolicyCompliance(OpenShift):
    """
    policy-review lab script for DO480
    """
    __LAB__ = "policy-review"
    
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
            {
                "label": "Project 'policy-review' is not present",
                "task": self._fail_if_exists,
                "name": "policy-review",
                "type": "Project",
                "api": "project.openshift.io/v1",
                "namespace": "",
                "fatal": True
            },
            {
                "label": "Adding cluster-admin Users",
                "task": self.run_playbook,
                "playbook": "ansible/policy-review/add-cluster-admin.yaml"
            },
            steps.run_command(label="Logging in to OCP4 hub cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            steps.run_command(label="Adding environment label to local-cluster", hosts=["workstation"], command="oc", options="label managedclusters local-cluster environment=stage --overwrite", prints="local-cluster"),
            steps.run_command(label="Adding environment label to managed-cluster", hosts=["workstation"], command="oc", options="label managedclusters managed-cluster environment=production --overwrite", prints="managed-cluster", failmsg="Import the managed-cluster into RHACM"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Starting")

    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            steps.run_command(label="Logging in to OCP4 hub cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            {
                "label": "Removing cluster-admin Users",
                "task": self.run_playbook,
                "playbook": "ansible/policy-review/remove-cluster-admin.yaml"
            },
            {
                "label": "Removing the policy-review namespace",
                "task": self._delete_resource,
                "kind": "Project",
                "api": "project.openshift.io/v1",
                "name": "policy-review",
                "namespace": None,
            },
            steps.run_command(label="Removing environment label from local-cluster", hosts=["workstation"], command="oc", options="label managedclusters local-cluster environment- --overwrite", returns="0"),
            steps.run_command(label="Removing environment label from managed-cluster", hosts=["workstation"], command="oc", options="label managedclusters managed-cluster environment- --overwrite", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Finishing")


    def grade(self):
        """
        Grade lab exercise.
        """
        items = [
            {
                "label": "Checking if project 'policy-review' exists",
                "task": self._fail_if_not_exists,
                "name": "policy-review",
                "type": "Project",
                "api": "project.openshift.io/v1",
                "namespace": "",
                "fatal": True
            },
            {
                "label": "Validating Namespace Policy for stage environment. This task takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/policy-review/namespace-policy-local-grade.yaml"
            },
            {
                "label": "Validating Namespace Policy for production environment. This task takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/policy-review/namespace-policy-grade.yaml"
            },
            {
                "label": "Checking Iam Policy for stage environment",
                "task": self.run_playbook,
                "playbook": "ansible/policy-review/iam-policy-local-grade.yaml"
            },
            {
                "label": "Checking Iam Policy for production environment",
                "task": self.run_playbook,
                "playbook": "ansible/policy-review/iam-policy-managed-grade.yaml"
            },
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
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
