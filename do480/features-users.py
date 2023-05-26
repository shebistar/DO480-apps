#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     features-users - DO480 Configure lab exercise script
#
# SYNOPSIS
#     features-users {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#  * Tue Jan  12 2022 Rafa Ruiz <rruizher@redhat.com>
#   - Adding check of OCP with DynoLabs functions
#  * Tue Jan  4 2022 Rafa Ruiz <rruizher@redhat.com>
#   - Checking RHACM with playbooks
#  * Tue Oct 26 2021 Alejandro Coma <acomabon@redhat.com>
#   - original code
#
#

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
features-users guided exercise.
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

class FeaturesUsers(OpenShift):
    """Activity class."""
    __LAB__ = "features-users"
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
                                           
            #steps.run_command(label="Logging in to IDM", hosts=IDM_SERVER, command="echo 'Redhat123@!' | kinit admin", options="", returns="0"),
            #do480_steps.add_ipa_user(self, uid="stage-admin", givenname="Stage", sn="Admin", password="redhat"),
            # do480_steps.add_ipa_group(self, name="deployers", users=["alice"]),
            
            do480_steps.add_ipa_user(self, uid="stage-admin", givenname="Stage", sn="Admin", password="redhat"),
            do480_steps.add_ipa_user(self, uid="prod-admin", givenname="Production", sn="Admin", password="redhat"),
            do480_steps.add_ipa_group(self, name="production-administrators", users=["prod-admin"]),
            do480_steps.add_ipa_group(self, name="stage-administrators", users=["stage-admin"]),
            {
                "label": "Syncing groups in RHOCP",
                "task": self.run_playbook,
                "playbook": "ansible/common/ocp_sync_ldap_groups.yaml"
            },
            steps.run_command(label="Creating user prod-admin in RHOCP", hosts=["workstation"], command="oc", options="login -u prod-admin -p redhat https://api.ocp4.example.com:6443", returns="0"),
            steps.run_command(label="Creating user stage-admin in RHOCP", hosts=["workstation"], command="oc", options="login -u stage-admin -p redhat https://api.ocp4.example.com:6443", returns="0"),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Starting")

    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login",options="-u admin -p redhat " + OCP4_API, returns="0"),
            do480_steps.remove_ipa_user(self, uid="stage-admin"),
            do480_steps.remove_ipa_user(self, uid="prod-admin"),
            do480_steps.remove_ipa_group(self, name="production-administrators"),
            do480_steps.remove_ipa_group(self, name="stage-administrators"),
            {
                "label": "Syncing groups in RHOCP",
                "task": self.run_playbook,
                "playbook": "ansible/common/ocp_sync_ldap_groups.yaml"
            },
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Finishing")
