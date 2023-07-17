#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     policy-compliance - DO480 Configure lab exercise script
#
# SYNOPSIS
#     policy-compliance {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#   * Wed 05 Jan 2022 Harpal Singh <harpasin@redhat.com>
#   - added ansible playbook to remove compliance operator
#   * Wed 23 Nov 2021 Harpal Singh <harpasin@redhat.com>
#   - added ocp module and tasks
#   * Wed 11 Nov 2021 Harpal Singh <harpasin@redhat.com>
#   - original code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
policy-compliance guided exercise.
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

labname = 'policy-compliance'
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost","workstation"]

class PolicyCompliance(OpenShift):
    """
    policy-compliance lab script for DO480
    """
    __LAB__ = "policy-compliance"
    
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
            steps.run_command(label="Project `openshift-compliance` is not present", hosts=["workstation"], command="oc", options="get projects openshift-compliance", returns="1", failmsg="The openshift-compliance Project already exists, please delete it or run 'lab finish policy-compliance' before starting this GE"),
            steps.run_command(label="Logging in to OCP4 hub cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            steps.run_command(label="Adding location label to managed-cluster", hosts=["workstation"], command="oc", options="label managedclusters managed-cluster location=APAC --overwrite", prints="managed-cluster", failmsg="Import the managed-cluster into RHACM"),
            {
                "label": "Project 'policy-compliance' is not present",
                "task": self._fail_if_exists,
                "name": "policy-compliance",
                "type": "Project",
                "api": "project.openshift.io/v1",
                "namespace": "",
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
            steps.run_command(label="Logging in to OCP4 hub cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            {
                "label": "Removing the policy-compliance namespace",
                "task": self._delete_resource,
                "kind": "Project",
                "api": "project.openshift.io/v1",
                "name": "policy-compliance",
                "namespace": None,
            },
            steps.run_command(label="Removing location label", hosts=["workstation"], command="oc", options="label managedclusters managed-cluster location- --overwrite", returns="0"),
            steps.run_command(label="Logging in to OCP4 managed cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_MNG_API, returns="0"),
            {
                "label": "Removing the compliance operator. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/policy-compliance/compliance_remove.yaml",
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