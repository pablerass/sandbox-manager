"""Sandbox manager common utils module."""
import logging
import paramiko
import time

WAIT_TIME = 15
MAX_TRIES = 12


# SSH funcions
def connect_ssh(host_name, user, key_file, key_pass):
    """Create an SSH connection.

    Waits a determined time until the connection is available.

    :param host_name: The host to connect.
    :type host_name: str

    :param user: The user to use in the connection.
    :type user: str
    """
    logger = logging.getLogger('ec-sb-mgr.utils.connect_ssh')

    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Get SSH key
    ssh_key = paramiko.RSAKey.from_private_key_file(key_file,
                                                    password=key_pass)
    # Connect to SSH host
    num_tries = 0
    while True:
        logger.debug('Trying to connect to %s (%i/%i)', host_name, num_tries,
                     MAX_TRIES)
        try:
            # Try to connect
            ssh.connect(host_name, username=user, pkey=ssh_key)
            logger.debug('Connected to %s server', host_name)
            break
        except paramiko.AuthenticationException as e:
            # Authentication error
            logger.error('User %s authentication error connecting to %s', user,
                         host_name)
            raise e
        except Exception as e:
            # Exit if already tried enought
            if num_tries > MAX_TRIES:
                logger.error('Could not connect to %s server after %i attempt',
                             host_name, MAX_TRIES)
                raise e
            # Wait and try again
            logger.debug('Coult not connect to %s server, waiting %i seconds',
                         host_name, WAIT_TIME)
            time.sleep(WAIT_TIME)
            num_tries += 1

    # Return SSH connection
    return ssh
