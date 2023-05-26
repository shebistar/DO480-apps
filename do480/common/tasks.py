"""
Common task functions ready to be reused in CL260 lab steps
"""

import time
import logging
import subprocess
import collections
import paramiko
import re

from typing import Dict, List

from .logger import lab_logger
from .constants import (
    USER_NAME, SSH_KEY)

def run_log(*args, **kwargs):
    """
    Run any command logging stdout to the configured file.
    Logging should be initalized first through config_stdoutlog.
    This function makes use of the subprocess module.
    """

    # Run the command through subprocess
    output = subprocess.run(*args, **kwargs)

    # Log to the configured stdout file
    logging.info('Run command: ' + ' '.join(map(str, args)))
    if output.stdout:
        logging.info("STDOUT: \n\n" + output.stdout.decode("utf-8"))

    if output.stderr:
        logging.info("STDERR: \n\n" + output.stderr.decode("utf-8"))

    return output

def run_command(item: Dict):
    """
    Run a command on target host(s).
    The following parameters are used:
    * ``command`` is the command to be run
    * ``host`` is the list of hosts where the command should be run through ssh
    * (optional) ``prints`` allows the user to look for a specific string at
      the stdout
    * (optional) ``returns`` allows the user to look for a specific return code
      at the output of the command
    * (optional) ``root`` allows to execute the ssh command using the root user
    When running in workstation (localhost), the following parameters are used:
    * (optional) ``root`` allows to execute the ssh command using the root user
    When running in remote servers, the following parameters are used:
    * ``username`` username to execute the remote command
    * ``password`` password to authenticate the remote user
    * (optional) ``sshkey`` is the used for the ssh connection.
        Defaults to /home/student/.ssh/lab_rsa if not provided.
    """

    if "hosts" not in item:
        item["failed"] = True
        item["msgs"] = [{"text": "No hosts are given as an argument"}]
        e = Exception
        item["exception"] = {
            "name": e.__class__.__name__,
            "message": str(e),
        }

        return item

    if "sshkey" not in item:
        sshkey = SSH_KEY
    else:
        sshkey: str = ''.join(item["sshkey"])

    host_list: str = item["hosts"]
    prints: str = item.get("prints")
    returns: int = item.get("returns")
    failmsg: str = item.get("failmsg")


    command = item["command"] + ' ' + item["options"]
    cmd: str = ''.join(command)

    # error_found and error_log will keep track of which target servers
    # fail to run the cmd
    error_found: bool = False
    error_log = []

    for target in host_list:
        try:
            # Running in workstation
            if (target == "localhost") or (target == "workstation"):
                args: List = []
                cmdoptions = cmd.split()
                for i in cmdoptions:
                    args.append(i)

                output = run_log(args,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

                item["failed"] = False

            # Running in remote server
            else:
                if "username" not in item:
                    item["failed"] = True
                    msg = "No username given as an argument"
                    item["msgs"] = [{"text": msg}]
                    e = Exception
                    item["exception"] = {
                        "name": e.__class__.__name__,
                        "message": str(e),
                    }
                    return item
                else:
                    user: str = ''.join(item["username"])
                    
                output = run_ssh(target, sshkey, cmd, user)

        except Exception as e:
            item["failed"] = True
            item["msgs"] = [{"text": str(cmd) + " was unsuccessful"}]
            item["exception"] = {
                "name": e.__class__.__name__,
                "message": str(e),
            }
            return item

        try:
            if returns:
                if int(returns) != int(output.returncode):
                    msg = "Command did not exit with the expected code at '" \
                     + target + "'"
                    error_log.append({"text": msg})
                    msg = "Expected: " + str(returns) + ", Received: " \
                        + str(output.returncode)
                    error_log.append({"text": msg})
                    msg = "stderr: " + str(output.stderr)
                    error_log.append({"text": msg})
                    msg = "Fix: " + str(failmsg)
                    error_log.append({"text": msg})
                    error_found = True

            if prints:
                ostr = str(output.stdout)
                r = re.compile(prints, re.IGNORECASE)
                m = r.search(ostr)
                if m:
                    pass
                else:
                    item["failed"] = True
                    error_found = True
                    error_log.append({"text": f"'{prints}' not found in command output at '{target}'"})
                    msg = "Fix: " + str(failmsg)
                    error_log.append({"text": msg})

            if error_found:
                item["msgs"] = error_log
                item["failed"] = True

        except AssertionError as err:
            item["failed"] = True
            item["msgs"] = [
                    {"text": str(err)}
            ]

            if output.stderr:
                item["msgs"].append({"text": f"Stderr: {output.stderr}"})


def run_ssh(hostname, sshkey, command, username):
    """
    Run an ssh command and returns stdout, stderr and exit status.
    """

    # exit $? needed to get the exit status of the command
    command_nout = command
    command = command + '; exit $?'

    # Start ssh session and make sure to add the corresponding ssh key
    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connection.connect(hostname, key_filename=sshkey,
                       username=username)

    # Execute the command
    stdin, stdout, stderr = connection.exec_command(command)

    # Save the exit status, stout, stderr of the command and close session
    returncode: int = stdout.channel.recv_exit_status()
    stdout: str = stdout.readlines()
    stderr: str = stderr.readlines()
    connection.close()

    # Create a namedtuple to match the run_log output
    sesion = collections.namedtuple('sesion', 'stdout stderr returncode')
    output = sesion(stdout=stdout, stderr=stderr, returncode=returncode)

    # Log to the configured stdout file
    cmd = 'Run ssh command on ' + hostname + ' as user ' + username + ': '
    cmd = cmd + command_nout

    logging.info(cmd)
    if stdout:
        logging.info('STDOUT: \n\n' + ''.join(stdout))

    if stderr:
        logging.info('STDERR: \n\n' + ''.join(stderr))

    return output
