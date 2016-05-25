"""Manage HAProxy access to sandboxes."""
from datetime import datetime
import glob
import logging
import os
import re

import paramiko

import sandbox_manager
import sandbox_manager.iaas as iaas

from sandbox_manager.conf import SandboxConfig
from sandbox_manager.utils import connect_ssh


def get_cookie_value(instance_name):
    """Generate the cookie value wich corresponds with the specified instance.

    :param instance_name: The instance to get its cookie value.
    :type instance_name: str
    """
    return iaas.get_instance_ip(iaas.get_instance(instance_name)).split('.')[3]


def _get_instance_file_name(instance_name):
    return HAPROXY_INSTANCE_CONF_PATTERN.format(instance=instance_name)


def add_instance(instance_name, duration, tags=[]):
    """Add an instance to HAProxy configuration with its metadata.

    Each instance is tagged with its duration and the specified tags.

    :param instance_name: The instance to configure.
    :type instance_name: str

    :param duration: The duration of the instance.
    :type duration: int

    :param tags: The list of tags to add to the instance configuration.
    :type tags: list(str)
    """
    logger = logging.getLogger('sb-mgr.proxy.haproxy.add_instance')

    # Define intance file name specific configuration file
    instance_file_name = _get_instance_file_name(instance_name)

    # Creates instance configuration HAProxy
    instance = iaas.get_instance(instance_name)
    instance_conf = ("  server {server_name} {instance_ip}:80 cookie "
                     "{cookie} check # {start_datetime} {duration} "
                     "{tags}\n").format(server_name=instance_name,
                                        instance_ip=iaas.get_instance_ip(
                                            instance),
                                        cookie=get_cookie_value(instance_name),
                                        start_datetime=datetime.now().
                                        isoformat(' '),
                                        duration=duration, tags=" ".join(tags))
    logger.debug('Instance %s HAProxy configuration line is %s', instance_name,
                 instance_conf)

    # Opens instance specific file and writes its content
    with open(instance_file_name, 'w') as instance_file:
        instance_file.write(instance_conf)
        logger.info('Added %s instance to HAProxy configuration',
                    instance_name)
        logger.debug('Created HAProxy configuration file %s',
                     instance_file_name)

    _update_haproxy_conf()


def remove_instance(instance_name):
    """Remove the specified instance from HAProxy configuration.

    :param instance_name: The instance to remove.
    :type instance_name: str
    """
    logger = logging.getLogger('sb-mgr.proxy.haproxy.remove_instance')

    # Delete instance specific file
    instance_file_name = _get_instance_file_name(instance_name)
    try:
        os.remove(instance_file_name)
        logger.info('Removed %s instance to HAProxy configuration',
                    instance_name)
        logger.debug('Deleted HAProxy configuration file %s',
                     instance_file_name)
    except FileNotFoundError:
        logger.warning('Instance %s HAProxy configuration file does not exist',
                       instance_name)
        logger.debug('HAProxy configuration file %s does not exists',
                     instance_file_name)

    # Update HAProxy configuration
    _update_haproxy_conf()


def list_instances():
    """List all HAProxy configuration file instances.

    :returns: A list of instances.
    :rtype: list[dict]
    """
    logger = logging.getLogger('sb-mgr.proxy.haproxy.list_instances')

    instances = []
    instance_files = glob.glob(HAPROXY_INSTANCE_CONF_FILES)
    logger.debug('Found %i instance configuration files', len(instance_files))

    # Extract data from instance configuration file
    for instance_file in instance_files:
        instance = _parse_instance_file(instance_file)
        instances.append(instance)

    return instances


def _parse_instance_file(instance_conf_file):
    # TODO: Check more than one configuration per file
    # Get file content
    logger = logging.getLogger('sb-mgr.proxy.haproxy._parse_instance_file')

    with open(instance_conf_file, "r") as conf_file:
        instance_conf = conf_file.readline()

    # Parse file configuration and return it
    instance_conf_re = ("^  server (?P<server_name>.+) (?P<instance_ip>.+):80 "
                        "cookie (?P<cookie_value>[0-9]+) check "
                        "# (?P<start_datetime>.+) (?P<duration>[0-9]+) "
                        "(?P<tags>.+ ?)*$")
    instance_conf_match = re.match(instance_conf_re, instance_conf)
    logger.debug('Configuration parsing: "%s" > "%s"', instance_conf_re,
                 instance_conf)
    if not instance_conf_match:
        logger.error('Unable to parse configuration content from file %s',
                     instance_conf_file)
        return {
            'server_name': os.path.basename(instance_conf_file).split('.')[0],
            'error': 'Unsable to parse configuration'}
    else:
        instance = instance_conf_match.groupdict()
        instance["tags"] = instance["tags"].split(' ')
        return instance


def _update_haproxy_conf():
    """Generate the HAProxy sandbox configuration and updates it.

    Uses a SSH connection, authenticated with private key, to deploy created
    configuration in the corresponding.
    """
    # TODO: Check if conf file is locked
    # TODO: Try to avoid multiple simultáneus execution of this code
    logger = logging.getLogger('sb-mgr.proxy.haproxy._update_conf')

    # Load configuration
    logger.debug('Loading configuration')
    try:
        conf = SandboxConfig()
        HAPROXY_SERVER = conf.get('proxy', 'host_name')
        HAPROXY_USER = conf.get('proxy', 'user')
        HAPROXY_KEY_FILE_NAME = conf.get('proxy', 'key_file')
        HAPROXY_KEY_FILE = os.path.join(sandbox_manager.CONF_DIR,
                                        HAPROXY_KEY_FILE_NAME)
        HAPROXY_KEY_FILE_PASS = conf.get('proxy', 'key_file_pass')

        COOKIE_NAME = conf.get('proxy', 'cookie_name')

        HAPROXY_REMOTE_CONF_FILE = '/etc/haproxy/conf.d/sandboxes.cfg'
        HAPROXY_REMOTE_CONF_TMP_FILE = '/tmp/sandboxes.cfg.tmp'

        HAPROXY_HEADER_FILE = os.path.join(sandbox_manager.CONF_DIR,
                                           'haproxy.cfg.header')
        HAPROXY_CONF_FILE = os.path.join(sandbox_manager.TMP_DIR, 'haproxy.cfg.local')
        HAPROXY_INSTANCE_CONF_PATTERN = os.path.join(sandbox_manager.TMP_DIR,
                                                     '{instance}.cfg.instance')
        HAPROXY_INSTANCE_CONF_FILES = os.path.join(sandbox_manager.TMP_DIR,
                                                   '*.cfg.instance')
    except Exception as e:
        logger = logging.getLogger('sb-mgr.proxy.haproxy.conf')
        logger.critical('Unable to load configuration')
        raise e

    # Check if header configuration file exists
    if not os.path.exists(HAPROXY_HEADER_FILE):
        raise Exception(("Required configuration header file {file_} does not "
                         "exists"), format(file_=HAPROXY_HEADER_FILE))

    # Get instance configuration files
    instance_files = glob.glob(HAPROXY_INSTANCE_CONF_FILES)

    # Generate all configuration files to join
    src_conf_files = [HAPROXY_HEADER_FILE] + instance_files
    logger.debug('"%s" HAProxy configuration files available',
                 ', '.join(src_conf_files))

    # Join configuration file
    with open(HAPROXY_CONF_FILE, 'w') as conf_file:
        for src_conf_file_name in src_conf_files:
            with open(src_conf_file_name) as src_conf_file:
                for line in src_conf_file:
                    conf_file.write(line)

    # Update configuration on HAProxy server
    _reload_haproxy_service()


def _reload_haproxy_service():
    logger = logging.getLogger('sb-mgr.proxy.haproxy._update_service')

    # Load configuration
    logger.debug('Loading configuration')
    try:
        conf = SandboxConfig()
        HAPROXY_SERVER = conf.get('proxy', 'host_name')
        HAPROXY_USER = conf.get('proxy', 'user')
        HAPROXY_KEY_FILE_NAME = conf.get('proxy', 'key_file')
        HAPROXY_KEY_FILE = os.path.join(sandbox_manager.CONF_DIR,
                                        HAPROXY_KEY_FILE_NAME)
        HAPROXY_KEY_FILE_PASS = conf.get('proxy', 'key_file_pass')

        COOKIE_NAME = conf.get('proxy', 'cookie_name')

        HAPROXY_REMOTE_CONF_FILE = '/etc/haproxy/conf.d/sandboxes.cfg'
        HAPROXY_REMOTE_CONF_TMP_FILE = '/tmp/sandboxes.cfg.tmp'

        HAPROXY_HEADER_FILE = os.path.join(sandbox_manager.CONF_DIR,
                                           'haproxy.cfg.header')
        HAPROXY_CONF_FILE = os.path.join(sandbox_manager.TMP_DIR, 'haproxy.cfg.local')
        HAPROXY_INSTANCE_CONF_PATTERN = os.path.join(sandbox_manager.TMP_DIR,
                                                     '{instance}.cfg.instance')
        HAPROXY_INSTANCE_CONF_FILES = os.path.join(sandbox_manager.TMP_DIR,
                                                   '*.cfg.instance')
    except Exception as e:
        logger = logging.getLogger('sb-mgr.proxy.haproxy.conf')
        logger.critical('Unable to load configuration')
        raise e

    with connect_ssh(HAPROXY_SERVER, HAPROXY_USER, HAPROXY_KEY_FILE,
                     HAPROXY_KEY_FILE_PASS) as conn:
        # Copy configuration file to HAProxy server
        sftp_conn = paramiko.SFTPClient.from_transport(conn.get_transport())
        sftp_conn.put(HAPROXY_CONF_FILE, HAPROXY_REMOTE_CONF_TMP_FILE)
        logger.debug('Updated sandbox HAProxy configuration temporal file %s',
                     HAPROXY_REMOTE_CONF_TMP_FILE)
        stdin, stdout, stderr = conn.exec_command(
            'sudo cp {tmp_file} {conf_file}'.format(
                tmp_file=HAPROXY_REMOTE_CONF_TMP_FILE,
                conf_file=HAPROXY_REMOTE_CONF_FILE))
        logger.debug('HAProxy temporal configuration copied to production')

        # Reload configuration
        stdin, stdout, stderr = conn.exec_command(
            'sudo service haproxy reload')
        if stdout.channel.recv_exit_status():
            raise Exception('HAProxy service could not be reloaded')
        logger.info('Reloaded HAProxy configuration')
