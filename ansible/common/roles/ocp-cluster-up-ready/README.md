Role Name
=========

The OpenShift cluster is not immediately available as soon as the classroom environment is running.
Use this role to verify that the OpenShift cluster is ready for lab exercises.

Courses that use a shared OpenShift cluster should not need to use this role.

Courses using this role:
  - DO370

Requirements
------------

This role uses the redhat.openshift and kubernetes.core Ansible collections.
Your DLE must pre-install these Ansible collections on workstation.

Role Variables
--------------

This is an example of role variable that can be place in a file in host_vars.
The "host" variable is the URL of the OpenShift API.
The "kubeconfig" variable is the path to a kubeconfig file that provides system:admin access.
If the play targets the utility machine, then this is the path on the utility machine.

        ocp_cluster:
          host: "https://api.ocp4.example.com:6443"
          kubeconfig: /home/lab/ocp4/auth/kubeconfig
          validate_certs: False

Dependencies
------------

This role requires that you access the OpenShift cluster as a user with the cluster-admin role. The lab user on the utility machine can run commands as the system:admin user using the kubeconfig file located at /home/lab/ocp4/auth/kubeconfig.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - name: Check if OpenShift Cluster is up
      hosts: utility
      remote_user: lab
      gather_facts: False
      module_defaults:
        group/k8s:
          host: "{{ ocp_cluster['host'] }}"
          kubeconfig: "{{ ocp_cluster['kubeconfig'] }}"
          validate_certs: "{{ ocp_cluster['validate_certs'] }}"
      roles:
         - role: ocp-cluster-up-ready

License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
