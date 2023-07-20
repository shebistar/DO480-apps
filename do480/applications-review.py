#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     applications-review - DO480 Configure lab exercise script
#
# SYNOPSIS
#     applications-review {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
applications-review guided exercise.
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


labname = 'applications-review'
SKU = labconfig.get_course_sku().upper()
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost","workstation"]


class ApplicationsReview(OpenShift):
    """
    applications-review lab script for DO480
    """
    __LAB__ = "applications-review"

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
            steps.run_command(label="Logging in to OCP4 managed cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_MNG_API, returns="0"),
            steps.run_command(label="Project `mysql` is not present", hosts=["workstation"], command="oc", options="get projects mysql", returns="1", failmsg="The mysql project already exists, please delete it or run 'lab finish applications-review' before starting this GE"),
            steps.run_command(label="Logging in to OCP4 hub cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            steps.run_command(label="Verifying the availability of the local-cluster", hosts=["workstation"], command="oc", options="get managedclusters", prints="local-cluster", failmsg="Create the MultiClusterHub object"),
            steps.run_command(label="Verifying the availability of the managed-cluster", hosts=["workstation"], command="oc", options="get managedclusters", prints="managed-cluster", failmsg="Import the managed-cluster into RHACM"),
            {
                "label": "Copy exercise files",
                "task": labtools.copy_lab_files,
                "lab_name": self.__LAB__,
                "fatal": True
            },
            {
                "label": "Project 'mysql' is not present",
                "task": self._fail_if_exists,
                "name": "mysql",
                "type": "Project",
                "api": "project.openshift.io/v1",
                "namespace": "",
                "fatal": True
            },
            steps.run_command(label="Removing the env label from managed-cluster", hosts=["workstation"], command="oc", options="label managedclusters managed-cluster env- --overwrite", returns="0"),
            steps.run_command(label="Removing the env label from local-cluster", hosts=["workstation"], command="oc", options="label managedclusters local-cluster env- --overwrite", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Starting")

    def grade(self):
        """
        Grade lab exercise.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 hub cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat https://api.ocp4.example.com:6443", returns="0"),
            {
                "label": "Validating env label. This task takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/applications-review/label.yaml"
            },
            {
                "label": "Verifying that the APAC deployment has the correct image",
                "task": self.run_playbook,
                "playbook": "ansible/applications-review/image_tag_156.yaml"
            },
            {
                "label": "Verifying that the EMEA deployment has the correct image",
                "task": self.run_playbook,
                "playbook": "ansible/applications-review/image_tag_152.yaml"
            },
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        ui = Console(items)
        ui.run_items(action="Grading")
        ui.report_grade()


    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            steps.run_command(label="Verifying connectivity to the OCP4 managed cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_MNG_API, returns="0"),
            steps.run_command(label="Removing the mysql namespace", hosts=["workstation"], command=this_path + "/files/applications-review/delete_project.sh", options="", returns="0"),
            steps.run_command(label="Verifying connectivity to the OCP4 cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            {
                "label": "Removing the mysql namespace",
                "task": self._delete_resource,
                "kind": "Project",
                "api": "project.openshift.io/v1",
                "name": "mysql",
                "namespace": None,
            },
            steps.run_command(label="Removing the environment label from managed-cluster", hosts=["workstation"], command="oc", options="label managedclusters managed-cluster env- --overwrite", returns="0"),
            steps.run_command(label="Removing the environment label from local-cluster", hosts=["workstation"], command="oc", options="label managedclusters local-cluster env- --overwrite", returns="0"),
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