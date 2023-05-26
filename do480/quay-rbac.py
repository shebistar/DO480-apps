#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     quay-rbac - DO480 Configure lab exercise script
#
# SYNOPSIS
#     quay-rbac {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps


import os
import sys
import logging
import requests

from .common import steps
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

class QuayRbac(OpenShift):
    """Activity class."""
    __LAB__ = "quay-rbac"
    # Get the OCP host and port from environment variables
    OCP_API = {
        "user": os.environ.get("OCP_USER", "admin"),
        "password": os.environ.get("OCP_PASSWORD", "redhat"),
        "host": os.environ.get("OCP_HOST", "api.ocp4.example.com"),
        "port": os.environ.get("OCP_PORT", "6443"),
    }

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
                "fatal": True,
            },
            {
                "label": "Checking that the OCP hub is up and ready",
                "task": self.run_playbook,
                "playbook": "ansible/common/ocp_cluster_up_and_ready.yaml",
                "fatal": True,
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
                "label": "Removing Quay CRD. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_remove.yaml",
                "vars": {"remove_quay_operator": False,},
                "fatal": True
            },
            {
                "label": "Installing Quay. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_install.yaml",
                "fatal": True
                
            },
            do480_steps.add_ipa_user(self, uid="alice", givenname="Alice", sn="Deployments", password="redhat"),
            do480_steps.add_ipa_user(self, uid="bob", givenname="Bob", sn="Developments", password="redhat"),
            do480_steps.add_ipa_group(self, name="deployers", users=["alice"]),
            do480_steps.add_ipa_group(self, name="developers", users=["bob"]),
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Starting")

    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            {
                "label": "Removing Quay CRD. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_remove.yaml",
                "vars": {"remove_quay_operator": False,},
            },
            {
                "label": "Installing Quay. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_install.yaml",
                
            },
            do480_steps.remove_ipa_user(self, uid="alice"),
            do480_steps.remove_ipa_user(self, uid="bob"),
            do480_steps.remove_ipa_group(self, name="deployers"),
            do480_steps.remove_ipa_group(self, name="developers"),
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login", options="-u admin -p redhat " + OCP4_API, returns="0"),
        ]
        Console(items).run_items(action="Finishing")
