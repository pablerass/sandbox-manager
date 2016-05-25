"""Manage mock sandboxes."""
import logging


def launch_instance():
    """Mock launch instance method."""
    logger = logging.getLogger('sb-mgr.iaas.mock.launch_instance')

    logger.debug("Mock run")


def instance_exists(instance):
    """Mock instance exists method."""
    logger = logging.getLogger('sb-mgr.iaas.mock.instance_exists')

    logger.debug("Mock run")


def get_instance(instance_name):
    """Mock get instance metthod."""
    logger = logging.getLogger('sb-mgr.iaas.mock.get_instance')

    logger.debug("Mock run")


def delete_instance(instance):
    """Mock delete instance method."""
    logger = logging.getLogger('sb-mgr.iaas.mock.delete_instance')

    logger.debug("Mock run")


def get_instance_ip(instance):
    """Mock get instance ip."""
    return instance
