"""This module provides dummy, insecure versions of Tin sandboxing functions.

For production and production-like environments, the sandboxing submodule (.sandboxing/__init__.py)
should be used. If this module is used as a fallback, running submissions will still not work due to
a FileNotFoundError. However, the rest of Tin's functionality should work as expected (albeit
without secure sandboxing).

This module is able to serve as a fallback due to PEP 420's import processing specification. See:
https://peps.python.org/pep-0420/#specification.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


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
    logger.warning("Tin is using the dummy sandboxing module. This is insecure.")
    return command_args
