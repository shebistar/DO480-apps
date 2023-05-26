#
# Copyright 2021 Red Hat, Inc.
#
# NAME
#     operate-review - DO480 Configure lab exercise script
#
# SYNOPSIS
#     operate-review {start|finish}
#
#        start   - prepare the system for starting the lab
#        finish  - perform post-exercise cleanup steps
#
# CHANGELOG
#   * Thu 02 Jun 2022 Harpal Singh <harpasin@redhat.com>
#   - original code

"""
Lab script for DO480 Configure.
This module implements the start and finish functions for the
operate-review guided exercise.
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

labname = 'operate-review'
this_path = os.path.abspath(os.path.dirname(__file__))
_targets = ["localhost","workstation"]

class PolicyCompliance(OpenShift):
    """
    operate-review lab script for DO480
    """
    __LAB__ = "operate-review"
    
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
                "label": "Project 'operate-review' is not present",
                "task": self._fail_if_exists,
                "name": "operate-review",
                "type": "Project",
                "api": "project.openshift.io/v1",
                "namespace": "",
                "fatal": True
            },
            {
                "label": "Ensuring that Quay registry and the Quay operator are not present. This command can take more than 5 minutes. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_remove.yaml"
            },
            {
                "label": "Project 'rhacs-install' is not present from the previous exercise. Deleting if present.",
                "task": self.run_playbook,
                "playbook": "ansible/operate-review/policy_namespace_remove.yaml"

            },
            {
                "label": "Checking that RHACS is installed on hub cluster. Deleting if present. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/operate-review/rhacs_hub_remove.yaml"

            },
            {
                "label": "Checking that RHACS is installed on managed cluster. Deleting if present. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/operate-review/rhacs_managed_remove.yaml"

            },
            {
                "label": "Installing Quay. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_install.yaml",
                
            },
            {
                "label": "Copy exercise files",
                "task": labtools.copy_lab_files,
                "lab_name": self.__LAB__,
                "fatal": True,
            },
            {
                "label": "Deploying RHACM policies to install the RHACS operator, central and secured cluster",
                "task": self._start_create_resources,
                "resources_file": "rhacs-install.yaml",
                "fatal": True,
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
                "label": "Removing the operate-review namespace",
                "task": self._delete_resource,
                "kind": "Project",
                "api": "project.openshift.io/v1",
                "name": "operate-review",
                "namespace": None,
            },
            {
                "label": "Ensuring that Quay registry and the Quay operator are not present. This command can take more than 5 minutes. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/common/quay_remove.yaml"
            },
            {
                "label": "Checking that RHACS is installed on hub cluster. Deleting if present. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/operate-review/rhacs_hub_remove.yaml"

            },
            {
                "label": "Checking that RHACS is installed on managed cluster. Deleting if present. This command takes a while. Do not interrupt the execution.",
                "task": self.run_playbook,
                "playbook": "ansible/operate-review/rhacs_managed_remove.yaml"

            },
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        Console(items).run_items(action="Finishing")


    def grade(self):
        """
        Grade lab exercise.
        """
        items = [
            {
                "label": "Checking if project 'operate-review' exists",
                "task": self._fail_if_not_exists,
                "name": "operate-review",
                "type": "Project",
                "api": "project.openshift.io/v1",
                "namespace": "",
                "fatal": True
            },
            {
                "label": "Checking cluster init secrets in the hub cluster",
                "task": self.run_playbook,
                "playbook": "ansible/operate-review/secret_check_hub.yaml"

            },
            {
                "label": "Checking cluster init secrets in the managed cluster",
                "task": self.run_playbook,
                "playbook": "ansible/operate-review/secret_check_managed.yaml"

            },
            {
                "label": "Checking if secret 'quaysecret' exists",
                "task": self.run_playbook,
                "playbook": "ansible/operate-review/quaysecret_check.yaml"

            },
            {
                "label": "Checking if application 'hello-central' is working",
                "task": self.run_playbook,
                "playbook": "ansible/operate-review/app_test.yaml"

            },
            steps.run_command(label="Logging out", hosts=["workstation"], command="oc", options="logout", returns="0")
        ]
        ui = Console(items)
        ui.run_items(action="Grading")
        ui.report_grade()
    
        # Create resources from YAML file
    def _start_create_resources(self, item):
        logging.debug("_start_create_resources()")
        lab_name = type(self).__LAB__
        lab_dir = os.path.join(
            pkg_resources.resource_filename(__name__, "materials"),
            "solutions",
            lab_name,
        )
        NAMESPACE = "rhacs-install"
        item["msgs"] = []
        try:
            # Create Project
            project = {
                "apiVersion": "project.openshift.io/v1",
                "kind": "Project",
                "metadata": {
                    "name": NAMESPACE,
                },
            }
            logging.info(
                "Create {}/{}".format(project["kind"], project["metadata"]["name"])
            )
            resource = self.oc_client.resources.get(
                api_version=project["apiVersion"], kind=project["kind"]
            )
            resource.create(body=project, namespace=None)
            item["msgs"].append({"text": "Project"})
            # Create resources from composite yaml file
            resources_file = os.path.join(lab_dir, item["resources_file"])
            logging.info("Creating resources from: {}".format(resources_file))
            with open(resources_file) as input_file:
                content = input_file.read()
                documents = yaml.load_all(content, Loader=yaml.SafeLoader)
                for element in documents:
                    logging.info(
                        "Create {}/{}".format(
                            element["kind"], element["metadata"]["name"]
                        )
                    )
                    resource = self.oc_client.resources.get(
                        api_version=element["apiVersion"], kind=element["kind"]
                    )
                    resource.create(body=element, namespace=NAMESPACE)
            item["msgs"].append({"text": "RHACS operator and RHACS resources"})
            item["failed"] = False
        except Exception as e:
            exception_name = e.__class__.__name__
            if (exception_name == "ConflictError"):
                logging.info("Element already exists")
                item["failed"] = False
            else:
                item["failed"] = True
                item["msgs"] = [{"text": "Could not create resources"}]
                item["exception"] = {
                    "name": exception_name,
                    "message": str(e),
                }
        return item["failed"]


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
