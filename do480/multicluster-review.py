#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     multicluster-review - DO480 Configure lab exercise script
#
# SYNOPSIS
#     multicluster-review {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#  * Tue Jan  13 2022 Rafa Ruiz <rruizher@redhat.com>
#   - Adding check of OCP with DynoLabs functions
#   * Tue Nov 25 2021 Alejandro Coma <acomabon@redhat.com>
#   - original code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
multicluster-review guided exercise.
"""

import os
import subprocess
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
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost","workstation"]

class MultiClusterReview(OpenShift):
    """Activity class."""
    __LAB__ = "multicluster-review"
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
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            {
                "label": "Verifying that the RHACM Operator is not present. Deleting if present. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/acm_remove.yaml",
                "fatal": True
            },
            {
                "label": "Verifying that the RHACM cluster roles are not present in the managed cluster. Deleting if present.",
                "task": self.run_playbook,
                "playbook": "ansible/multicluster-acm/remove_roles.yaml"
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
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            {
                    "label": "Remove lab files",
                    "task": labtools.delete_workdir,
                    "lab_name": self.__LAB__,
                    "fatal": True
            },
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Finishing")

    def grade(self):
        """
        Grade lab exercise.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            steps.run_command(label="Verifying RHACM Operator deployment", hosts=["workstation"], command="oc get csv -n open-cluster-management", options="", prints="Succeeded", failmsg="Install the RHACM Operator"),
            steps.run_command(label="Verifying RHACM MultiClusterHub deployment", hosts=["workstation"], command="oc", options="get multiclusterhub -n open-cluster-management", prints="Running", failmsg="Create the MultiClusterHub object"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        ui = Console(items)
        ui.run_items(action="Grading")
        ui.report_grade()
