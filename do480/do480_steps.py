import pkg_resources

from ansible_runner import interface

from labs.common import tasks


@tasks.task
def _run_module(lab, module, host_pattern=None, **module_args):
    if host_pattern is None:
        host_pattern = "utility"
    runner = interface.run(
        module=module,
        host_pattern=host_pattern,
        project_dir=pkg_resources.resource_filename(lab.__module__, "ansible/common"),
        module_args=" ".join([f"{k}={v}" for k,v in module_args.items()]),
        settings={"suppress_ansible_output": True},
    )
    if runner.rc != 0:
        raise Exception("Error running module")


IPA_COMMON_ARGS = {
    "ipa_pass": "Redhat123@!",
    "ipa_host": "idm.ocp4.example.com",
    "validate_certs": "no",
    "ipa_user": "admin",
}


def add_ipa_user(lab, uid, givenname, sn, password):
    return {
        "label": f"Creating user {uid} on IdM",
        "task": _run_module(lab, "ipa_user", uid=uid, givenname=givenname, sn=sn, password=password, **IPA_COMMON_ARGS)
    }


def remove_ipa_user(lab, uid):
    return {
        "label": f"Removing user {uid} from IdM",
        "task": _run_module(lab, "ipa_user", uid=uid, state="absent", **IPA_COMMON_ARGS)
    }


def add_ipa_group(lab, name, users):
    return {
        "label": f"Creating group {name} on IdM",
        "task": _run_module(lab, "ipa_group", name=name, user=",".join(users), **IPA_COMMON_ARGS)
    }


def remove_ipa_group(lab, name):
    return {
        "label": f"Removing group {name} from IdM",
        "task": _run_module(lab, "ipa_group", name=name, state="absent", **IPA_COMMON_ARGS)
    }
