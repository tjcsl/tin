import os

import psutil

from django.conf import settings


def get_assignment_sandbox_args(
    command_args,
    *,
    network_access: bool,
    direct_network_access: bool = False,
    whitelist=None,
    read_only=None,
    extra_firejail_args=None,
):
    return get_sandbox_args(
        command_args,
        "grader",
        network_access=network_access,
        direct_network_access=direct_network_access,
        whitelist=whitelist,
        read_only=read_only,
        extra_firejail_args=extra_firejail_args,
    )


def get_action_sandbox_args(
    command_args,
    *,
    network_access: bool,
    direct_network_access: bool = False,
    whitelist=None,
    read_only=None,
    extra_firejail_args=None,
):
    return get_sandbox_args(
        command_args,
        "actions",
        network_access=network_access,
        direct_network_access=direct_network_access,
        whitelist=whitelist,
        read_only=read_only,
        extra_firejail_args=extra_firejail_args,
    )


def get_sandbox_args(
    command_args,
    profile,
    *,
    network_access: bool,
    direct_network_access: bool = False,
    whitelist=None,
    read_only=None,
    extra_firejail_args=None,
):

    firejail_args = [
        "firejail",
        "--quiet",
        "--profile={}".format(os.path.join(os.path.dirname(__file__), f"{profile}.profile")),
    ]

    if whitelist:
        for path in whitelist:
            firejail_args.append("--whitelist={}".format(path))

    if read_only:
        for path in read_only:
            firejail_args.append("--read-only={}".format(path))

    if extra_firejail_args:
        firejail_args.extend(extra_firejail_args)

    if network_access:
        if not direct_network_access:
            addrs = psutil.net_if_addrs()
            interfaces = list(addrs.keys())

            if "lo" in interfaces:
                interfaces.remove("lo")

            def score_interface(name):
                if name.startswith(("lxc", "lxd")):
                    return -2
                elif name.startswith("tap"):
                    return -1
                elif name.startswith(("wlp", "wlo", "eth", "eno", "enp")):
                    # Prefer Ethernet interfaces, but also prefer interfaces with IP addresses
                    # with netmasks set
                    return (
                        1
                        + name.startswith("e")
                        + sum(addr.netmask is not None for addr in addrs[name])
                    )
                else:
                    return 0

            if interfaces:
                firejail_args.append("--net={}".format(max(interfaces, key=score_interface)))
                firejail_args.append("--netfilter")
                for nameserver in settings.SUBMISSION_NAMESERVERS:
                    firejail_args.append("--dns={}".format(nameserver))
            else:
                firejail_args.append("--net=none")
    else:
        firejail_args.append("--net=none")

    return [*firejail_args, *command_args]
