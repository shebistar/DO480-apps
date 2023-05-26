#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     quay-review - DO480 Configure lab exercise script
#
# SYNOPSIS
#     qay-review {start|grade|finish}
#
#        start   - prepare the system for starting the lab
#        grade   - grades the lab
#        finish  - perform post-exercise cleanup steps

import os
import sys
import logging
import pkg_resources
import requests
import subprocess
from labs.common import steps
from ocp.utils import OpenShift
from labs import labconfig
from labs.common.userinterface import Console
from labs.common import labtools
from kubernetes.client.exceptions import ApiException
from .common.constants import USER_NAME, IDM_SERVER, OCP4_API, OCP4_MNG_API

SKU = labconfig.get_course_sku().upper()
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost","workstation"]

class QuayReview(OpenShift):
    """Activity class."""
    __LAB__ = "quay-review"
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
            {
                "label": "Ensuring that Quay registry and the Quay operator are not present. This command can take more than 5 minutes. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_remove.yaml"
            },
            {
                "label": "Copy exercise files",
                "task": labtools.copy_lab_files,
                "lab_name": self.__LAB__,
                "fatal": True
            },
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc logout", returns="0", shell=True)
        ]
        Console(items).run_items(action="Starting")

    def finish(self):
        """
        Perform any post-lab cleanup tasks.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_API, returns="0", shell=True),
            {
                "label": "Removing Quay. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_remove.yaml",
            },
            {
                "label": "Remove lab files",
                "task": labtools.delete_workdir,
                "lab_name": self.__LAB__,
                "fatal": True
            },
        ]
        Console(items).run_items(action="Finishing")

    def grade(self):
        """
        Grade lab exercise.
        """
        items = [
            steps.run_command(label="Verifying connectivity to OCP4 cluster", hosts=["workstation"], command="oc login -u admin -p redhat " + OCP4_API, returns="0", shell=True),
            steps.run_command(label="Verifying Quay operator is deployed", hosts=["workstation"], command="oc get deployment -n openshift-operators quay-operator.v3.6.4 -o json | jq .status.readyReplicas | grep 1", returns="0", shell=True),
            steps.run_command(label="Verifying registry namespace exists", hosts=["workstation"], command="oc get namespace registry", returns="0", shell=True),
            steps.run_command(label="Verifying Quay deployments are ready", hosts=["workstation"], command="oc get deployment -n registry central-quay-app -o json | jq .status.readyReplicas | grep 2", returns="0", shell=True),
            steps.run_command(label="Check that the /home/student/quayadmin_token file exists", hosts=["workstation"], command="test -f /home/student/quayadmin_token", returns="0", shell=True),
            {
                "label": "Check that the /home/student/quayadmin_token file is a valid token",
                "task": self.check_token,
            },
            {
                "label": "Check that finance organization exists",
                "task": self.check_org,
            },
            {
                "label": "Check that finance/budget-app-dev repository exists and contains a latest tag",
                "task": self.check_repo,
            },
        ]
        ui = Console(items)
        ui.run_items(action="Grading")
        ui.report_grade()

    def check_token(self, item):
        self.make_quay_api_request("superuser/users/")

    def check_org(self, item):
        self.make_quay_api_request("organization/finance")

    def check_repo(self, item):
        repo = self.make_quay_api_request("repository/finance/budget-app-dev")
        assert repo["tags"]["latest"], "no tag latest found"

    def make_quay_api_request(self, path):
        token = self.get_token()
        response = requests.get(
            f"https://central-quay-registry.apps.ocp4.example.com/api/v1/{path}",
            verify=False,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"}).json()
        assert 'error_message' not in response, f"Error from API {response}"
        return response

    def get_token(self):
        with open("/home/student/quayadmin_token", encoding="UTF8") as f:
            return f.read().strip()
