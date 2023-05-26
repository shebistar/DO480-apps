#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     features-console - DO480 Configure lab exercise script
#
# SYNOPSIS
#     features-console {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#   * Thu Jan 13 2022 Rafa Ruiz
#  - Adding check of OCP with DynoLabs functions
#   * Tue Nov 5 2021 Rafa Ruiz
#   - original code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
features-console guided exercise.
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
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost","workstation"]

class FeaturesConsole(OpenShift):
    """Activity class."""
    __LAB__ = "features-console"
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
            
            #steps.run_command(label="Verifying connectivity to OCP4 managed cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_MNG_API, returns="0"),
            
            
           
            steps.run_command(label="Verifying the availability of the managed-cluster", hosts=["workstation"], command="oc", options="get managedclusters", prints="managed-cluster", failmsg="Import the managed-cluster into RHACM"),
            steps.run_command(label="Creating all namespaces and deployments", hosts=["workstation"], command=this_path + "/files/features-console/create_all_persistence.sh", options="", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Starting")

    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
            steps.run_command(label="Deleting all namespaces and deployments. This command takes a while. Do not interrupt the execution.", hosts=["workstation"], command=this_path + "/files/features-console/delete_all_persistence.sh", options="", returns="0"),
        ]
        Console(items).run_items(action="Finishing")
