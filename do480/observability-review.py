#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     observability-review - DO480 Configure lab exercise script
#
# SYNOPSIS
#     observability-review {start|finish}
#
#        start   - prepare the system for starting the lab
#        grade   - grades the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#   * Fri Feb 4 2022 Rafa Ruiz <rruizher@redhat.com>
#   - Adapted to use Ansible checks
#   * Tue Nov 9 2021 Alejandro Coma <acomabon@redhat.com>
#   - original code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
observability-review guided exercise.
"""

import os
import sys
import logging
import pkg_resources
import requests
import yaml
import subprocess
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

class ObservabilityReview(OpenShift):
    """Activity class."""
    __LAB__ = "observability-review"
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
            #steps.run_command(label="Verifying that the observability service is not enabled", hosts=["workstation"], command="oc", options="get mco observability", returns="1", failmsg="The observability service is already enabled. Please run the 'lab finish observability-install' command before starting again."),
            {
                "label": "Verifying that the observability service is not enabled. Deleting if present. This command can take a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/acm_remove_observability.yaml"
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
        get_obs = subprocess.run('/usr/bin/oc get mco observability', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if get_obs.returncode == 0:
            items = [
                steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
                {
                    "label": "Verifying that the observability service is not enabled. Deleting if present. This command takes a while. Do not interrupt the execution.",
                    "task": self.run_playbook,
                    "playbook": "ansible/common/acm_remove_observability.yaml"
                },
                {
                    "label": "Remove lab files",
                    "task": labtools.delete_workdir,
                    "lab_name": self.__LAB__,
                    "fatal": True
                },
                steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
            ]
            Console(items).run_items(action="Finishing")
        else:
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
            steps.run_command(label="Verifying that the observability service is enabled", hosts=["workstation"], command="oc", options="get mco observability", returns="0", failmsg="The observability service is not enabled. Follow the instructions in the guided exercise to enable it."),
            steps.run_command(label="Verifying that the alert rule is created", hosts=["workstation"], command="oc", options="get ConfigMap thanos-ruler-custom-rules -n open-cluster-management-observability", returns="0", failmsg="MemoryRequested-45 alert rule not found. Follow the instructions in the guided exercise to enable it.")
        ]
        ui = Console(items)
        ui.run_items(action="Grading")
        ui.report_grade()
