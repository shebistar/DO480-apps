"""
Common lab steps for DO480 lab exercises
"""

from os import posix_fallocate
from typing import List, Dict

from labs.common import labtools

from . import tasks

from .constants import (
    USER_NAME, SSH_KEY, IDM_SERVER, OCP4_API, OCP4_MNG_API, OCP4_SNO_API,
    REGISTRY_USERNAME, REGISTRY_PASSWORD)


#def config_stdoutlog(filename: str):
#    return {
#        "label": "Configure logging",
#        "task": tasks.config_stdoutlog(filename),
#    }


def check_host_reachable(targets: List[str]):
    return {
        "label": "Checking lab systems",
        "task": labtools.check_host_reachable,
        "hosts": targets,
        "fatal": True
    }


def run_command(label,hosts,command,**kwargs):
    return {
        "label": label,
        "task": tasks.run_command,
        "hosts": hosts,
        "username": USER_NAME,
        "command": command,
        "returns": kwargs.get("returns",0),
        "options": kwargs.get("options",''),
        "prints": kwargs.get("prints",''),
        "fatal": kwargs.get("fatal",False),
        "failmsg": kwargs.get("failmsg",''),
    }
