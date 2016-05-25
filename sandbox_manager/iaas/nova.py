"""Manage nova sandboxes."""
import logging
import os
import random
import string
import time

from novaclient.v1_1 import client as nova
import novaclient

import sandbox_manager

from sandbox_manager.conf import SandboxConfig

SANDBOX_PREFIX = "sandbox"


# Instance functions
def _connect_nova():
    logger = logging.getLogger('sb-mgr.iaas.nova._connect_nova')

    # Load configuration
    logger.debug('Loading configuration')
    try:
        conf = SandboxConfig()
        NOVA_AUTH_URL = conf.get('nova', 'auth_url')
        NOVA_PROJECT_ID = conf.get('nova', 'project_id')
        NOVA_USER = conf.get('nova', 'project_user')
        NOVA_PASS = conf.get('nova', 'project_pass')
    except Exception as e:
        logger.critical('Unable to load Nova connection configuration')
        raise e

    # Connect to Nova
    conn = nova.Client(username=NOVA_USER,
                       api_key=NOVA_PASS,
                       project_id=NOVA_PROJECT_ID,
                       auth_url=NOVA_AUTH_URL)
    logger.info('Connected to OpenStack project %s', NOVA_PROJECT_ID)
    logger.debug('OpenStack connection user is %s', NOVA_USER)
    logger.debug('OpenStack auth URL is %s', NOVA_AUTH_URL)

    # Return Nova connection
    return conn


def launch_instance():
    """Launch a new sandbox instance. Waits until it is active.

    :returns: The new instance.
    :rtype: novaclient.servers.Server
    """
    WAIT_TIME = 10
    MAX_TRIES = 12

    logger = logging.getLogger('sb-mgr.iaas.nova.launch_instance')

    # Load configuration
    logger.debug('Loading configuration')
    try:
        conf = SandboxConfig()
        SANDBOX_USER = conf.get('sandbox', 'user')
        SANDBOX_KEY_NAME = conf.get('sandbox', 'key_name')
        SANDBOX_KEY_FILE_NAME = conf.get('sandbox', 'key_file')
        SANDBOX_KEY_FILE = os.path.join(sandbox_manager.CONF_DIR,
                                        SANDBOX_KEY_FILE_NAME)
        SANDBOX_KEY_FILE_PASS = conf.get('sandbox', 'key_file_pass')

        SANDBOX_FLAVOR = conf.get_int('sandbox', 'flavor')
        # TODO: Extract image id from highest version of image name
        SANDBOX_IMAGE = conf.get('sandbox', 'image')
        SANDBOX_NET_NAME = conf.get('sandbox', 'net_name')
    except Exception as e:
        logger.critical('Unable to load Nova connection configuration')
        raise e

    with _connect_nova() as conn:
        try:
            # Launch the instance
            instance_name = _new_instance_name(SANDBOX_PREFIX)
            instance = conn.servers.create(name=instance_name,
                                           image=SANDBOX_IMAGE,
                                           flavor=SANDBOX_FLAVOR,
                                           key_pair=SANDBOX_KEY_NAME,
                                           loaded=True)
            logger.info('Created instance %s, wait until it becomes active',
                        instance.name)
            logger.debug('Instance %s id     : %s', instance.name, instance.id)
            logger.debug('Instance %s image  : %s', instance.name,
                         SANDBOX_IMAGE)
            logger.debug('Instance %s flavor : %s', instance.name,
                         SANDBOX_FLAVOR)
            logger.debug('Instance %s keypair: %s', instance.name,
                         SANDBOX_KEY_NAME)
        except novaclient.exceptions.OverLimit as e:
            logger.error('Could not launch instance, over quota')
            raise e

        # Wait until instance becomes active
        num_tries = 0
        while not instance.status == 'ACTIVE' and num_tries < MAX_TRIES:
            logger.debug(("Waiting for %s instance (%i/%i), waiting %i "
                          "seconds, now %s"), instance.name, num_tries,
                         MAX_TRIES, WAIT_TIME, instance.status)
            time.sleep(WAIT_TIME)
            logger.debug('Reloading %s instance', instance.name)
            instance = conn.servers.find(name=instance_name)
            num_tries += 1

        if not instance.status == 'ACTIVE':
            raise Exception('Instance {instance} has not become available'.
                            format(instance=instance.name))

        logger.debug('Instance %s is now active', instance.name)

        # Return the instance name
        return instance_name


def instance_exists(instance_name):
    """Check if an instance exists in Nova with the same name.

    :param instance: The name of the instance to check.
    :type instance: str

    :returns: If an instant with the specified name exists.
    :rtype: bool
    """
    logger = logging.getLogger('sb-mgr.iaas.nova.instance_exists')

    # Check if instance exists
    try:
        get_instance(instance_name)
        logger.debug('Instance %s exists', instance_name)
        return True
    except novaclient.exceptions.NotFound:
        return False


def get_instance(instance_name):
    """Retrieve instance from Nova using its name.

    :param instance_name: The name of the instance to retrieve.
    :type instance_name: str

    :returns: The instance with the specified name.
    :rtype: novaclient.servers.Server
    """
    logger = logging.getLogger('sb-mgr.iaas.nova.get_instance')

    with _connect_nova() as conn:
        try:
            # Get the instance
            logger.debug('Searching instance {instance}'.format(
                         instance=instance_name))
            instance = conn.servers.find(name=instance_name)
            logger.debug('Loaded instance %s', instance.name)

            # Return the instance
            return instance
        except novaclient.exceptions.NotFound as e:
            logger.warning('Instance %s does not exist', instance_name)
            raise e


def terminate_instance(instance):
    """Terminate the specified instance.

    :param instance: The instance name object to terminate.
    :type instance: str or novaclient.servers.Server
    """
    logger = logging.getLogger('sb-mgr.iaas.nova.terminate_instance')

    # Check if the argument is an instance or a string
    if isinstance(instance, str):
        instance_name = instance
        instance = get_instance(instance_name)
    else:
        instance_name = instance.name

    # Delete the instance
    instance.delete()
    logger.info('Instance %s terminated', instance_name)


def _random_string(length, char_set=string.hexdigits):
    return ''.join([random.choice(char_set) for i in range(length)])


def _random_instance_name(prefix, length):
    return '{pre}-{suf}'.format(pre=prefix,
                                suf=_random_string(length - len(prefix) - 1))


def _new_instance_name(prefix, length=12):
    logger = logging.getLogger('sb-mgr.iaas.nova._new_instance_name')

    # Returns an non used instance name
    instance_name = _random_instance_name(prefix, length)
    while instance_exists(instance_name):
        instance_name = _random_instance_name(prefix, length)
    logger.debug('Generated %s random instance name', instance_name)

    return instance_name


def get_instance_ip(instance):
    """Get instance ip.

    :param instance: The instance name or objetc to get its ip.
    :type instance: str or novaclient.servers.Server

    :returns: The instance ip.
    :rtype: str
    """
    logger = logging.getLogger('sb-mgr.iaas.nova.get_instance_ip')

    # Check if the argument is an instance or a string
    if isinstance(instance, str):
        instance_name = instance
        instance = get_instance(instance_name)
    else:
        instance_name = instance.name

    # Get instance ip
    instance_ip = instance.networks[SANDBOX_NET_NAME][0]
    logger.debug('Instance %s ip is %s', instance_name, instance_ip)
    return instance_ip
