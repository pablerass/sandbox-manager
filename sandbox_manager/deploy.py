"""Deploy to sandbox methods."""
import logging
import os
import paramiko

import sandbox_manager
import sandbox_manager.iaas

from sandbox_manager.conf import SandboxConfig
from sandbox_manager.utils import connect_ssh

SANDBOX_DEPLOY_TARGET = '/tmp/target'
SANDBOX_DEPLOY_SCRIPT = '/opt/deploy.sh {remote_dir}'.format(
                        remote_dir=SANDBOX_DEPLOY_TARGET)
SANDBOX_DEPLOY_LOG = '/tmp/deploy.log'


# Deployment functions
def deploy_app(instance, artifacts, args=''):
    """Deploy the specified artifacts into an sandbox instance.

    Uses the ``/opt/deploy.sh`` that must be contained in the sandbox instance
    and creates a log file ``/opt/deploy.log``.

    Waits deploy command has finished, to work properly, it should not end
    until the sandboxed application is started.

    :param instance: The deploy destination instance.
    :type instance: str

    :param artifacts: The list of artifacts to deploy.
    :type artifacts: list(str)
    """
    logger = logging.getLogger('sb-mgr.deploy_app')

    # Load configuration
    logger.debug('Loading configuration')
    try:
        conf = SandboxConfig()
        SANDBOX_USER = conf.get('sandbox', 'user')
        SANDBOX_KEY_FILE_NAME = conf.get('sandbox', 'key_file')
        SANDBOX_KEY_FILE = os.path.join(sandbox_manager.CONF_DIR,
                                        SANDBOX_KEY_FILE_NAME)
        SANDBOX_KEY_FILE_PASS = conf.get('sandbox', 'key_file_pass')
    except Exception as e:
        logger.critical('Unable to load configuration')
        raise e

    logger.info('Beggining artifacts deploy')
    sandbox_ip = sandbox_manager.iaas.get_instance_ip(instance)
    logger.debug('Trying to connect to sandbox %s', sandbox_ip)
    with connect_ssh(sandbox_ip, SANDBOX_USER, SANDBOX_KEY_FILE,
                     SANDBOX_KEY_FILE_PASS) as conn:
        # Create artifacts dest file
        stdin, stdout, stderr = conn.exec_command('mkdir {dst_dir}'.format(
            dst_dir=SANDBOX_DEPLOY_TARGET))
        if stdout.channel.recv_exit_status():
            raise Exception('{sandbox} dir {dir_} could not be created'.format(
                            sandbox=instance.name, dir_=SANDBOX_DEPLOY_TARGET))
        logger.debug('%s dir %s created', sandbox_ip, SANDBOX_DEPLOY_TARGET)

        # Load all artifact files
        sftp_conn = paramiko.SFTPClient.from_transport(conn.get_transport())
        logger.info('Uploading artifacts...')
        for artifact_file in artifacts:
            # Extract the file name and create dst file
            dst_file = os.path.join(SANDBOX_DEPLOY_TARGET,
                                    os.path.split(artifact_file)[1])
            sftp_conn.put(artifact_file, dst_file)
            logger.debug('Artifact %s copied to %s in sandbox %s',
                         artifact_file, dst_file, instance.name)

        # Launch deploy script
        deploy_command = 'sudo {command} {args} &> {log}'.format(
            command=SANDBOX_DEPLOY_SCRIPT,
            args=" ".join(['"{arg}"'.format(arg=arg) for arg in args]),
            log=SANDBOX_DEPLOY_LOG)
        logger.info('Executing deploy...')
        logger.debug('Executing "%s" on sandbox %s', deploy_command,
                     sandbox_ip)
        stdin, stdout, stderr = conn.exec_command(deploy_command)
        if stdout.channel.recv_exit_status():
            raise Exception('Deploy command {command} failed'.format(
                            command=deploy_command))
        logger.info('Artifacts deploy completed')
