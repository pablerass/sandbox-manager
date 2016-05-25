"""Manage mock access to sandboxes."""
import logging


def get_cookie_value(instance_name):
    """Mock get cookie value method"""
    logger = logging.getLogger('sb-mgr.proxy.mock.launch_instance')

    logger.debug("Mock run")


def add_instance(instance_name, duration, tags=[]):
    """Mock add instance to proxy method."""
    logger = logging.getLogger('sb-mgr.proxy.mock.add_instance')

    logger.debug("Mock execution")


def remove_instance(instance_name):
    """Mock remove instance from proxy method.
    """
    logger = logging.getLogger('sb-mgr.proxy.mock.remove_instance')

    logger.debug("Mock execution")


def list_instances():
    """Mock list all instance file instances."""
    logger = logging.getLogger('sb-mgr.proxy.mock.list_instances')

    logger.debug("Mock execution")
